from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from project.server.models import AnalysisResult


class LocalFrameStorage:
    """Persist frames and analysis metadata under a local output directory."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def save_image(self, event_id: str, image_bytes: bytes, content_type: str) -> Path:
        suffix = self._suffix_for_content_type(content_type)
        path = self.output_dir / 'images' / f'{event_id}{suffix}'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(image_bytes)
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
