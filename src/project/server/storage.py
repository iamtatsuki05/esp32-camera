from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    from project.server.models import AnalysisResult


class LocalFrameStorage:
    """Persist frames and analysis metadata under a local output directory."""

    def __init__(self, output_dir: str | Path, save_jpeg_quality: int | None = None) -> None:
        self.output_dir = Path(output_dir)
        self.save_jpeg_quality = save_jpeg_quality

    def save_image(self, event_id: str, image_bytes: bytes, content_type: str) -> Path:
        suffix = self._suffix_for_content_type(content_type)
        path = self.output_dir / 'images' / f'{event_id}{suffix}'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self._prepare_image_bytes(image_bytes, content_type))
        return path

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
