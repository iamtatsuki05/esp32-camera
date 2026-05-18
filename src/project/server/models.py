from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Literal

from pydantic import BaseModel, Field


class FrameInput(BaseModel):
    """Raw frame received from ESP32-CAM or a local smoke test."""

    image_bytes: bytes
    content_type: str = 'image/jpeg'
    camera_id: str = 'esp32-cam'


class Detection(BaseModel):
    """Normalized detection result from a YOLO-compatible analyzer."""

    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox_xyxy: tuple[float, float, float, float]
    class_id: int | None = None
    track_id: str | None = None
    track_label: str | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    duration_seconds: float | None = None


class PersonTrack(BaseModel):
    """Lifecycle summary for one tracked person."""

    track_id: str
    track_label: str
    first_seen_at: datetime
    last_seen_at: datetime
    duration_seconds: float
    missed_seconds: float = 0.0


class UploadResult(BaseModel):
    """Result of local dry-run or future external upload."""

    status: Literal['dry-run', 'uploaded', 'skipped', 'failed']
    destination: str
    path: str | None = None
    message: str | None = None


class AnalysisResult(BaseModel):
    """Stored analysis event returned by the server API."""

    event_id: str
    camera_id: str
    captured_at: datetime
    analyzer: str
    detections: list[Detection]
    person_count: int = 0
    active_person_count: int = 0
    active_tracks: list[PersonTrack] = Field(default_factory=list)
    ended_tracks: list[PersonTrack] = Field(default_factory=list)
    content_type: str
    image_path: str | None = None
    video_path: str | None = None
    video_frame_index: int | None = None
    result_path: str | None = None
    upload_path: str | None = None
    upload: UploadResult = Field(
        default_factory=lambda: UploadResult(status='skipped', destination='none'),
    )
