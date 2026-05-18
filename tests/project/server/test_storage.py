from pathlib import Path

from project.server.sample_images import SMOKE_JPEG
from project.server.storage import LocalFrameStorage


def test_local_storage_preserves_image_bytes_by_default(tmp_path: Path) -> None:
    storage = LocalFrameStorage(output_dir=tmp_path)

    path = storage.save_image('raw', SMOKE_JPEG, 'image/jpeg')

    assert path.read_bytes() == SMOKE_JPEG


def test_local_storage_can_reencode_jpeg_quality(tmp_path: Path) -> None:
    storage = LocalFrameStorage(output_dir=tmp_path, save_jpeg_quality=40)

    path = storage.save_image('quality40', SMOKE_JPEG, 'image/jpeg')

    assert path.read_bytes().startswith(b'\xff\xd8\xff')
    assert path.read_bytes() != SMOKE_JPEG
