import json
from pathlib import Path

from project.server.analyzers import MockYoloAnalyzer
from project.server.models import FrameInput
from project.server.pipeline import AnalysisPipeline
from project.server.sample_images import SMOKE_JPEG
from project.server.storage import LocalFrameStorage
from project.server.uploaders import DryRunUploader


def test_pipeline_saves_frame_result_and_dry_run_upload(tmp_path: Path) -> None:
    pipeline = AnalysisPipeline(
        analyzer=MockYoloAnalyzer(),
        storage=LocalFrameStorage(output_dir=tmp_path),
        uploader=DryRunUploader(output_dir=tmp_path),
    )

    result = pipeline.process(
        FrameInput(
            image_bytes=SMOKE_JPEG,
            content_type='image/jpeg',
            camera_id='esp32-test',
        ),
    )

    assert result.camera_id == 'esp32-test'
    assert result.analyzer == 'mock-yolo'
    assert result.upload.status == 'dry-run'
    assert len(result.detections) == 1
    assert result.video_path is not None
    assert result.video_frame_index == 0
    assert result.result_path is not None
    assert result.upload_path is not None
    pipeline.storage.close()
    assert Path(result.video_path).is_file()
    assert Path(result.result_path).is_file()
    assert Path(result.upload_path).is_file()

    dry_run_payload = json.loads(Path(result.upload_path).read_text(encoding='utf-8'))
    assert dry_run_payload['upload']['status'] == 'dry-run'
    assert dry_run_payload['upload_path'] == result.upload_path


def test_pipeline_tracks_person_count_and_person_labels(tmp_path: Path) -> None:
    pipeline = AnalysisPipeline(
        analyzer=MockYoloAnalyzer(detections_per_frame=2, label='person'),
        storage=LocalFrameStorage(output_dir=tmp_path),
        uploader=DryRunUploader(output_dir=tmp_path),
    )

    first = pipeline.process(
        FrameInput(
            image_bytes=SMOKE_JPEG,
            content_type='image/jpeg',
            camera_id='esp32-test',
        ),
    )
    second = pipeline.process(
        FrameInput(
            image_bytes=SMOKE_JPEG,
            content_type='image/jpeg',
            camera_id='esp32-test',
        ),
    )

    assert first.person_count == 2
    assert first.active_person_count == 2
    assert [d.track_label for d in first.detections] == ['person A', 'person B']
    assert second.person_count == 2
    assert second.active_person_count == 2
    assert [d.track_label for d in second.detections] == ['person A', 'person B']
