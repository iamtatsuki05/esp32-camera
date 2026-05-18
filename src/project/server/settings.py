from __future__ import annotations

from pathlib import Path  # noqa: TC003
from typing import Any, Literal

from pydantic import BaseModel, Field

from project.common.utils.file.config import load_config
from project.env import PACKAGE_DIR


class ServerSettings(BaseModel):
    """Runtime settings for local development and ESP32-CAM ingestion."""

    host: str = '127.0.0.1'
    port: int = Field(default=8000, ge=1, le=65535)
    output_dir: Path = PACKAGE_DIR / 'data' / 'outputs'
    analyzer: Literal['mock-yolo', 'ultralytics-yolo'] = 'mock-yolo'
    yolo_model_path: str = 'yolov8n.pt'
    yolo_confidence_threshold: float = Field(default=0.25, ge=0.0, le=1.0)
    save_jpeg_quality: int | None = Field(default=None, ge=1, le=95)
    video_fps: float = Field(default=2.0, gt=0.0)
    uploader_mode: Literal['dry-run'] = 'dry-run'
    default_camera_id: str = 'esp32-cam'


def load_server_settings(
    config_path: str | Path | None = None,
    **overrides: Any,  # noqa: ANN401
) -> ServerSettings:
    """Load server settings from TOML/YAML/JSON/XML and explicit overrides."""
    values: dict[str, Any] = {}
    if config_path is not None:
        values.update(load_config(config_path))
    values.update({key: value for key, value in overrides.items() if value is not None})
    return ServerSettings(**values)
