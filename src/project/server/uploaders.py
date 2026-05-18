from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from project.server.models import AnalysisResult, UploadResult


class ResultUploader(Protocol):
    """Interface for future upload destinations."""

    def upload(self, result: AnalysisResult) -> UploadResult:
        """Upload or dry-run one result."""
        ...


class DryRunUploader:
    """Write the would-be upload payload locally without external network effects."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def upload(self, result: AnalysisResult) -> UploadResult:
        path = self.output_dir / 'uploads' / 'dry-run' / f'{result.event_id}.json'
        upload_result = UploadResult(
            status='dry-run',
            destination='local-dry-run',
            path=str(path),
            message='External upload is disabled by default.',
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = result.model_copy(update={'upload': upload_result, 'upload_path': str(path)}).model_dump(mode='json')
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return upload_result


def create_uploader(mode: str, output_dir: str | Path) -> ResultUploader:
    """Create an uploader by mode."""
    if mode == 'dry-run':
        return DryRunUploader(output_dir=output_dir)
    msg = f'Unsupported uploader mode: {mode}'
    raise ValueError(msg)
