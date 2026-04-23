from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from kalfiz_major_image.app import create_app
from kalfiz_major_image.config import Settings

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\x99c\xf8\xcf"
    b"\xc0\x00\x00\x03\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82"
)


def make_client(tmp_path: Path) -> TestClient:
    settings = Settings(media_root=tmp_path / "media")
    app = create_app(settings)
    return TestClient(app)


def test_health_endpoint(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_media_crud_flow(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    create_folder = client.post("/api/media/folder", json={"parent_path": "", "folder_name": "maps"})
    assert create_folder.status_code == 201

    upload = client.post(
        "/api/media/upload",
        data={"parent_path": "maps"},
        files={"file": ("battlemap.png", PNG_BYTES, "image/png")},
    )
    assert upload.status_code == 201
    assert upload.json()["entry"]["relative_path"] == "maps/battlemap.png"

    listing = client.get("/api/media", params={"path": "maps"})
    assert listing.status_code == 200
    assert listing.json()["entries"][0]["name"] == "battlemap.png"

    rename = client.patch(
        "/api/media/rename",
        json={"source_path": "maps/battlemap.png", "new_name": "forest"},
    )
    assert rename.status_code == 200
    assert rename.json()["entry"]["relative_path"] == "maps/forest.png"

    delete = client.request("DELETE", "/api/media", json={"target_path": "maps/forest.png"})
    assert delete.status_code == 204


def test_reject_invalid_extensions(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.post(
        "/api/media/upload",
        data={"parent_path": ""},
        files={"file": ("movie.gif", b"GIF89a", "image/gif")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported file type"


def test_display_state_apply_and_websocket(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    with client.websocket_connect("/ws/display") as websocket:
        initial = websocket.receive_json()
        assert initial["active_media_path"] is None

        apply_response = client.post(
            "/api/display-state/apply",
            json={"active_media_path": "maps/demo.png", "applied": True},
        )
        assert apply_response.status_code == 200

        updated = websocket.receive_json()
        assert updated["active_media_path"] == "maps/demo.png"
        assert updated["applied"] is True
