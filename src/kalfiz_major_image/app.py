from __future__ import annotations

import asyncio
import mimetypes
import subprocess
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, Request, Response, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import Settings, get_settings
from .display_state import DisplayStateStore
from .media import MediaLibrary
from .models import (
    ApplyDisplaySelection,
    CreateFolderRequest,
    DeleteMediaRequest,
    DisplayState,
    DisplayStateUpdate,
    ProvisionResult,
    ProvisionWifiRequest,
    RenameMediaRequest,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = PACKAGE_ROOT / "templates"
STATIC_DIR = PACKAGE_ROOT / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    media_library = MediaLibrary(app_settings.media_root)
    state_store = DisplayStateStore(
        DisplayState(
            grid={"size": app_settings.grid_default_size},
        )
    )

    app = FastAPI(title=app_settings.app_title)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.state.settings = app_settings
    app.state.media_library = media_library
    app.state.display_state = state_store

    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request) -> Response:
        if app_settings.runtime_mode == "provision":
            return templates.TemplateResponse(
                request=request,
                name="provision.html",
                context=_template_context(request),
            )
        return RedirectResponse(url="/control", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    @app.get("/control", response_class=HTMLResponse)
    async def control_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="control.html",
            context=_template_context(request),
        )

    @app.get("/display", response_class=HTMLResponse)
    async def display_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="display.html",
            context=_template_context(request),
        )

    @app.get("/provision", response_class=HTMLResponse)
    async def provision_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="provision.html",
            context=_template_context(request),
        )

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/status")
    async def status_summary() -> dict[str, object]:
        return {
            "runtime_mode": app_settings.runtime_mode,
            "media_root": str(app_settings.media_root),
            "display_state": state_store.snapshot().model_dump(mode="json"),
            "kiosk_url": app_settings.kiosk_url,
        }

    @app.get("/api/media")
    async def list_media(path: str = "") -> dict[str, object]:
        return {"entries": [entry.model_dump(mode="json") for entry in media_library.list_entries(path)]}

    @app.post("/api/media/upload", status_code=status.HTTP_201_CREATED)
    async def upload_media(
        parent_path: str = Form(default=""),
        file: UploadFile = File(...),
    ) -> dict[str, object]:
        entry = media_library.save_upload(parent_path, file)
        return {"entry": entry.model_dump(mode="json")}

    @app.post("/api/media/folder", status_code=status.HTTP_201_CREATED)
    async def create_folder(request_data: CreateFolderRequest) -> dict[str, object]:
        entry = media_library.create_folder(request_data.parent_path, request_data.folder_name)
        return {"entry": entry.model_dump(mode="json")}

    @app.patch("/api/media/rename")
    async def rename_media(request_data: RenameMediaRequest) -> dict[str, object]:
        entry = media_library.rename(request_data.source_path, request_data.new_name)
        return {"entry": entry.model_dump(mode="json")}

    @app.delete("/api/media")
    async def delete_media(request_data: DeleteMediaRequest) -> Response:
        media_library.delete(request_data.target_path)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/api/display-state")
    async def get_display_state() -> dict[str, object]:
        return state_store.snapshot().model_dump(mode="json")

    @app.put("/api/display-state")
    async def update_display_state(request_data: DisplayStateUpdate) -> dict[str, object]:
        state = await state_store.update(request_data)
        return state.model_dump(mode="json")

    @app.post("/api/display-state/apply")
    async def apply_display(request_data: ApplyDisplaySelection) -> dict[str, object]:
        state = await state_store.apply_selection(request_data.active_media_path)
        return state.model_dump(mode="json")

    @app.websocket("/ws/display")
    async def display_state_socket(websocket: WebSocket) -> None:
        await state_store.register(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            state_store.unregister(websocket)

    @app.get("/media/{relative_path:path}")
    async def serve_media(relative_path: str) -> FileResponse:
        file_path = media_library.file_path_for_serving(relative_path)
        return FileResponse(file_path, media_type=mimetypes.guess_type(file_path.name)[0])

    @app.post("/api/provision/wifi")
    async def provision_wifi(request_data: ProvisionWifiRequest) -> dict[str, object]:
        result = await _run_wifi_provision(app_settings, request_data)
        return result.model_dump(mode="json")

    @app.get("/api/provision/network-status")
    async def network_status() -> dict[str, str]:
        return {
            "mode": app_settings.runtime_mode,
            "hotspot_ssid": app_settings.hotspot_ssid,
            "hotspot_address": app_settings.hotspot_address,
        }

    return app


def _template_context(request: Request) -> dict[str, object]:
    app_settings: Settings = request.app.state.settings
    return {
        "request": request,
        "settings": app_settings,
    }


async def _run_wifi_provision(settings: Settings, request_data: ProvisionWifiRequest) -> ProvisionResult:
    if not settings.allow_network_mutations:
        return ProvisionResult(
            success=False,
            message="Network mutations are disabled. Set KALFIZ_ALLOW_NETWORK_MUTATIONS=true on the Pi to enable WiFi provisioning.",
        )

    command = ["nmcli", "device", "wifi", "connect", request_data.ssid]
    if request_data.password:
        command.extend(["password", request_data.password])

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode == 0:
        return ProvisionResult(success=True, message=stdout.decode().strip() or "Connected successfully")
    return ProvisionResult(success=False, message=stderr.decode().strip() or "Failed to connect")


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "kalfiz_major_image.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
    )


app = create_app()
