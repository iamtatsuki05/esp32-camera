from __future__ import annotations

import json
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
from PIL import Image

if TYPE_CHECKING:
    from project.server.models import AnalysisResult


@dataclass(frozen=True)
class VideoFrameRecord:
    """Location of a frame appended to a camera video."""

    video_path: str
    frame_index: int


class LocalFrameStorage:
    """Persist frames and analysis metadata under a local output directory."""

    def __init__(self, output_dir: str | Path, save_jpeg_quality: int | None = None, video_fps: float = 2.0) -> None:
        self.output_dir = Path(output_dir)
        self.save_jpeg_quality = save_jpeg_quality
        self.video_fps = video_fps
        self._video_sizes: dict[str, tuple[int, int]] = {}
        self._video_frames: dict[str, list[np.ndarray]] = {}
        self._frame_counts: dict[str, int] = {}

    def save_video_frame(self, camera_id: str, image_bytes: bytes, content_type: str) -> VideoFrameRecord:
        frame = self._decode_frame(image_bytes, content_type)
        safe_camera_id = self._safe_camera_id(camera_id)
        path = self.output_dir / 'videos' / f'{safe_camera_id}.avi'
        path.parent.mkdir(parents=True, exist_ok=True)

        frames = self._video_frames.get(safe_camera_id)
        if frames is None:
            height, width = frame.shape[:2]
            size = (width, height)
            self._video_sizes[safe_camera_id] = size
            frames = []
            self._video_frames[safe_camera_id] = frames
            self._frame_counts[safe_camera_id] = 0
        else:
            size = self._video_sizes[safe_camera_id]
            if (frame.shape[1], frame.shape[0]) != size:
                frame = cv2.resize(frame, size)

        frame_index = self._frame_counts[safe_camera_id]
        frames.append(frame)
        self._rewrite_video(path, frames, self._video_sizes[safe_camera_id])
        self._frame_counts[safe_camera_id] = frame_index + 1
        return VideoFrameRecord(video_path=str(path), frame_index=frame_index)

    def save_image(self, event_id: str, image_bytes: bytes, content_type: str) -> Path:
        suffix = self._suffix_for_content_type(content_type)
        path = self.output_dir / 'images' / f'{event_id}{suffix}'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self._prepare_image_bytes(image_bytes, content_type))
        return path

    def close(self) -> None:
        """Finalize open video files."""
        return

    def save_result(self, result: AnalysisResult) -> Path:
        path = self.output_dir / 'results' / f'{result.event_id}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = result.model_dump(mode='json')
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return path

    @staticmethod
    def _suffix_for_content_type(content_type: str) -> str:
        normalized = content_type.split(';', maxsplit=1)[0].strip().lower()
        if normalized == 'image/png':
            return '.png'
        return '.jpg'

    def _prepare_image_bytes(self, image_bytes: bytes, content_type: str) -> bytes:
        if self.save_jpeg_quality is None:
            return image_bytes
        normalized = content_type.split(';', maxsplit=1)[0].strip().lower()
        if normalized not in {'image/jpeg', 'image/jpg'}:
            return image_bytes
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        output = BytesIO()
        image.save(output, format='JPEG', quality=self.save_jpeg_quality, optimize=True)
        return output.getvalue()

    def _decode_frame(self, image_bytes: bytes, content_type: str) -> np.ndarray:
        prepared = self._prepare_image_bytes(image_bytes, content_type)
        image = Image.open(BytesIO(prepared)).convert('RGB')
        rgb = np.array(image)
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    @staticmethod
    def _safe_camera_id(camera_id: str) -> str:
        safe = re.sub(r'[^A-Za-z0-9_.-]+', '-', camera_id).strip('-._')
        return safe or 'camera'

    def _rewrite_video(self, path: Path, frames: list[np.ndarray], size: tuple[int, int]) -> None:
        writer = cv2.VideoWriter(
            str(path),
            cv2.VideoWriter.fourcc(*'MJPG'),
            self.video_fps,
            size,
        )
        if not writer.isOpened():
            msg = f'Failed to open video writer: {path}'
            raise RuntimeError(msg)
        try:
            for frame in frames:
                writer.write(frame)
        finally:
            writer.release()
