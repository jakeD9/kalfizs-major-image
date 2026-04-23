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
    device_hostname: str = "kalfiz"
    kiosk_url: str = "http://127.0.0.1:8000/display"
    hotspot_ssid: str = "Kalfiz-Setup"
    hotspot_address: str = "http://192.168.4.1:8000/provision"
    grid_default_size: int = 48

    @property
    def mdns_hostname(self) -> str:
        return f"{self.device_hostname}.local"

    @property
    def controller_url(self) -> str:
        return self._build_url("/control")

    @property
    def display_public_url(self) -> str:
        return self._build_url("/display")

    def _build_url(self, path: str) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        default_port = self.app_port in {80, 443}
        port_suffix = "" if default_port else f":{self.app_port}"
        return f"http://{self.mdns_hostname}{port_suffix}{normalized_path}"


def get_settings() -> Settings:
    return Settings()
