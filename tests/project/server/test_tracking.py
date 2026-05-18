from datetime import UTC, datetime, timedelta

from project.server.models import Detection
from project.server.tracking import PersonTracker


def test_person_tracker_keeps_duration_until_track_expires() -> None:
    tracker = PersonTracker(max_missing_seconds=1.0)
    start = datetime(2026, 5, 18, 12, 0, 0, tzinfo=UTC)

    first = tracker.update(
        [Detection(label='person', confidence=0.9, bbox_xyxy=(0.1, 0.1, 0.3, 0.4))],
        now=start,
    )
    empty = tracker.update([], now=start + timedelta(seconds=0.5))
    expired = tracker.update([], now=start + timedelta(seconds=2.0))

    assert first.person_count == 1
    assert first.active_person_count == 1
    assert first.detections[0].track_label == 'person A'
    assert first.detections[0].duration_seconds == 0.0
    assert empty.person_count == 0
    assert empty.active_person_count == 1
    assert empty.active_tracks[0].track_label == 'person A'
    assert empty.active_tracks[0].duration_seconds == 0.5
    assert expired.person_count == 0
    assert expired.active_person_count == 0
    assert expired.ended_tracks[0].track_label == 'person A'
    assert expired.ended_tracks[0].duration_seconds == 2.0


def test_person_tracker_ignores_non_person_detections() -> None:
    tracker = PersonTracker()
    now = datetime(2026, 5, 18, 12, 0, 0, tzinfo=UTC)

    result = tracker.update(
        [
            Detection(label='person', confidence=0.9, bbox_xyxy=(0.1, 0.1, 0.3, 0.4)),
            Detection(label='chair', confidence=0.9, bbox_xyxy=(0.4, 0.4, 0.6, 0.7)),
        ],
        now=now,
    )

    assert result.person_count == 1
    assert result.detections[0].track_label == 'person A'
    assert result.detections[1].track_label is None
