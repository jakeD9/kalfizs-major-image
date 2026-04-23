from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class GridSettings(BaseModel):
    enabled: bool = False
    size: int = Field(default=48, ge=8, le=512)
    offset_x: int = Field(default=0, ge=-4096, le=4096)
    offset_y: int = Field(default=0, ge=-4096, le=4096)


class DisplayState(BaseModel):
    active_media_path: str | None = None
    pending_media_path: str | None = None
    applied: bool = False
    grid: GridSettings = Field(default_factory=GridSettings)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DisplayStateUpdate(BaseModel):
    pending_media_path: str | None = None
    active_media_path: str | None = None
    applied: bool | None = None
    grid: GridSettings | None = None


class ApplyDisplaySelection(BaseModel):
    active_media_path: str
    applied: bool = True


class MediaEntry(BaseModel):
    name: str
    relative_path: str
    kind: Literal["file", "folder"]
    parent_path: str
    size: int | None = None


class RenameMediaRequest(BaseModel):
    source_path: str
    new_name: str

    @field_validator("new_name")
    @classmethod
    def ensure_name_present(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("new_name must not be empty")
        return normalized


class DeleteMediaRequest(BaseModel):
    target_path: str


class CreateFolderRequest(BaseModel):
    parent_path: str = ""
    folder_name: str

    @field_validator("folder_name")
    @classmethod
    def ensure_folder_name_present(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("folder_name must not be empty")
        return normalized


class ProvisionWifiRequest(BaseModel):
    ssid: str
    password: str | None = None

    @field_validator("ssid")
    @classmethod
    def ensure_ssid_present(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("ssid must not be empty")
        return normalized


class ProvisionResult(BaseModel):
    success: bool
    message: str
