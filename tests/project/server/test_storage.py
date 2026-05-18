from pathlib import Path

from project.server.sample_images import SMOKE_JPEG
from project.server.storage import LocalFrameStorage


def test_local_storage_writes_video_frame_by_camera(tmp_path: Path) -> None:
    storage = LocalFrameStorage(output_dir=tmp_path)

    first = storage.save_video_frame(camera_id='esp32-test', image_bytes=SMOKE_JPEG, content_type='image/jpeg')
    second = storage.save_video_frame(camera_id='esp32-test', image_bytes=SMOKE_JPEG, content_type='image/jpeg')
    storage.close()

    assert first.video_path == second.video_path
    assert first.frame_index == 0
    assert second.frame_index == 1
    assert Path(first.video_path).is_file()
    assert Path(first.video_path).suffix == '.avi'


def test_local_storage_can_reencode_jpeg_quality_before_video_write(tmp_path: Path) -> None:
    storage = LocalFrameStorage(output_dir=tmp_path, save_jpeg_quality=40)

    prepared = storage._prepare_image_bytes(SMOKE_JPEG, 'image/jpeg')  # noqa: SLF001

    assert prepared.startswith(b'\xff\xd8\xff')
    assert prepared != SMOKE_JPEG
