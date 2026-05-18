from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from project.server.models import AnalysisResult, FrameInput
from project.server.tracking import PersonTracker

if TYPE_CHECKING:
    from project.server.analyzers import FrameAnalyzer
    from project.server.storage import LocalFrameStorage
    from project.server.uploaders import ResultUploader


class AnalysisPipeline:
    """Analyze, store, and dry-run upload one camera frame."""

    def __init__(
        self,
        *,
        analyzer: FrameAnalyzer,
        storage: LocalFrameStorage,
        uploader: ResultUploader,
        tracker: PersonTracker | None = None,
    ) -> None:
        self.analyzer = analyzer
        self.storage = storage
        self.uploader = uploader
        self.tracker = tracker or PersonTracker()

    def process(self, frame: FrameInput) -> AnalysisResult:
        event_id = uuid4().hex
        captured_at = datetime.now(tz=UTC)
        detections = self.analyzer.analyze(frame)
        tracking = self.tracker.update(detections, now=captured_at)
        video_frame = self.storage.save_video_frame(frame.camera_id, frame.image_bytes, frame.content_type)
        result = AnalysisResult(
            event_id=event_id,
            camera_id=frame.camera_id,
            captured_at=captured_at,
            analyzer=self.analyzer.name,
            detections=tracking.detections,
            person_count=tracking.person_count,
            active_person_count=tracking.active_person_count,
            active_tracks=tracking.active_tracks,
            ended_tracks=tracking.ended_tracks,
            content_type=frame.content_type,
            image_path=None,
            video_path=video_frame.video_path,
            video_frame_index=video_frame.frame_index,
        )
        result.result_path = str(self.storage.save_result(result))
        upload = self.uploader.upload(result)
        result.upload = upload
        result.upload_path = upload.path
        result.result_path = str(self.storage.save_result(result))
        return result
