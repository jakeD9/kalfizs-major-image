from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KALFIZ_",
        env_file=".env",
        extra="ignore",
    )

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_title: str = "Kalfiz Major Image"
    media_root: Path = Field(default=Path("media"))
    runtime_mode: str = "runtime"
    allow_network_mutations: bool = False
    kiosk_url: str = "http://127.0.0.1:8000/display"
    hotspot_ssid: str = "Kalfiz-Setup"
    hotspot_address: str = "http://192.168.4.1:8000/provision"
    grid_default_size: int = 48


def get_settings() -> Settings:
    return Settings()
