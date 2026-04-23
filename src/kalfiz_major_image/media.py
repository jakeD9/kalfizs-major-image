from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from .models import MediaEntry

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class MediaLibrary:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def list_entries(self, relative_path: str = "") -> list[MediaEntry]:
        directory = self.resolve_directory(relative_path)
        entries: list[MediaEntry] = []
        for item in sorted(directory.iterdir(), key=lambda path: (path.is_file(), path.name.lower())):
            rel = item.relative_to(self.root).as_posix()
            entries.append(
                MediaEntry(
                    name=item.name,
                    relative_path=rel,
                    kind="folder" if item.is_dir() else "file",
                    parent_path=relative_path,
                    size=item.stat().st_size if item.is_file() else None,
                )
            )
        return entries

    def create_folder(self, parent_path: str, folder_name: str) -> MediaEntry:
        parent = self.resolve_directory(parent_path)
        target = self._safe_child(parent, folder_name)
        if target.exists():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Folder already exists")
        target.mkdir(parents=False, exist_ok=False)
        return MediaEntry(
            name=target.name,
            relative_path=target.relative_to(self.root).as_posix(),
            kind="folder",
            parent_path=parent_path,
            size=None,
        )

    def save_upload(self, parent_path: str, upload: UploadFile) -> MediaEntry:
        if not upload.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing upload filename")
        parent = self.resolve_directory(parent_path)
        name = self._sanitize_name(upload.filename)
        extension = Path(name).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")
        target = self._safe_child(parent, name)
        if target.exists():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="File already exists")
        with target.open("wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
        return MediaEntry(
            name=target.name,
            relative_path=target.relative_to(self.root).as_posix(),
            kind="file",
            parent_path=parent_path,
            size=target.stat().st_size,
        )

    def rename(self, source_path: str, new_name: str) -> MediaEntry:
        source = self.resolve_path(source_path)
        safe_name = self._sanitize_name(new_name)
        extension = source.suffix.lower()
        target_name = safe_name
        if source.is_file():
            if Path(safe_name).suffix.lower() not in ALLOWED_EXTENSIONS:
                if Path(safe_name).suffix:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")
                target_name = f"{safe_name}{extension}"
        target = self._safe_child(source.parent, target_name)
        if target.exists():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Target already exists")
        source.rename(target)
        return MediaEntry(
            name=target.name,
            relative_path=target.relative_to(self.root).as_posix(),
            kind="folder" if target.is_dir() else "file",
            parent_path=target.parent.relative_to(self.root).as_posix() if target.parent != self.root else "",
            size=target.stat().st_size if target.is_file() else None,
        )

    def delete(self, target_path: str) -> None:
        target = self.resolve_path(target_path)
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

    def resolve_directory(self, relative_path: str) -> Path:
        target = self.resolve_path(relative_path) if relative_path else self.root
        if not target.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Directory not found")
        if not target.is_dir():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path is not a directory")
        return target

    def resolve_path(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()
        if not self._is_under_root(candidate):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path")
        if candidate == self.root and relative_path:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path")
        return candidate

    def file_path_for_serving(self, relative_path: str) -> Path:
        target = self.resolve_path(relative_path)
        if not target.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        if target.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")
        return target

    def _safe_child(self, parent: Path, name: str) -> Path:
        safe_name = self._sanitize_name(name)
        target = (parent / safe_name).resolve()
        if not self._is_under_root(target):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path")
        return target

    def _sanitize_name(self, name: str) -> str:
        candidate = Path(name.strip()).name
        if not candidate or candidate in {".", ".."}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid name")
        if "/" in candidate or "\\" in candidate:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid name")
        return candidate

    def _is_under_root(self, candidate: Path) -> bool:
        try:
            candidate.relative_to(self.root)
        except ValueError:
            return False
        return True
