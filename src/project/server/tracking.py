from __future__ import annotations

import string
from dataclasses import dataclass
from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, Field

from project.server.models import Detection, PersonTrack


class TrackingUpdate(BaseModel):
    """Tracking fields computed for one analyzed frame."""

    detections: list[Detection]
    person_count: int
    active_person_count: int
    active_tracks: list[PersonTrack] = Field(default_factory=list)
    ended_tracks: list[PersonTrack] = Field(default_factory=list)


@dataclass
class _TrackState:
    track_id: str
    track_label: str
    first_seen_at: datetime
    last_seen_at: datetime
    bbox_xyxy: tuple[float, float, float, float]


class PersonTracker:
    """Small centroid tracker for person counts and per-person durations."""

    def __init__(self, max_missing_seconds: float = 5.0, max_match_distance: float = 0.25) -> None:
        self.max_missing_seconds = max_missing_seconds
        self.max_match_distance = max_match_distance
        self._tracks: dict[str, _TrackState] = {}
        self._next_index = 0

    def update(self, detections: list[Detection], *, now: datetime) -> TrackingUpdate:
        matched_track_ids: set[str] = set()
        tracked_detections: list[Detection] = []
        ended_tracks: list[PersonTrack] = []

        for detection in detections:
            if detection.label != 'person':
                tracked_detections.append(detection)
                continue
            track = self._match_or_create_track(detection, matched_track_ids, now)
            matched_track_ids.add(track.track_id)
            track.last_seen_at = now
            track.bbox_xyxy = detection.bbox_xyxy
            tracked_detections.append(self._apply_track(detection, track, now))

        for track_id, track in list(self._tracks.items()):
            if track_id in matched_track_ids:
                continue
            missed_seconds = (now - track.last_seen_at).total_seconds()
            if missed_seconds > self.max_missing_seconds:
                ended_tracks.append(self._to_person_track(track, now))
                del self._tracks[track_id]

        active_tracks = [
            self._to_person_track(track, now)
            for track in self._tracks.values()
            if (now - track.last_seen_at).total_seconds() <= self.max_missing_seconds
        ]
        return TrackingUpdate(
            detections=tracked_detections,
            person_count=sum(1 for detection in detections if detection.label == 'person'),
            active_person_count=len(active_tracks),
            active_tracks=active_tracks,
            ended_tracks=ended_tracks,
        )

    def _match_or_create_track(
        self,
        detection: Detection,
        matched_track_ids: set[str],
        now: datetime,
    ) -> _TrackState:
        best_track: _TrackState | None = None
        best_distance = float('inf')
        for track in self._tracks.values():
            if track.track_id in matched_track_ids:
                continue
            distance = self._center_distance(detection.bbox_xyxy, track.bbox_xyxy)
            if distance < best_distance:
                best_distance = distance
                best_track = track
        if best_track is not None and best_distance <= self.max_match_distance:
            return best_track
        return self._create_track(detection, now)

    def _create_track(self, detection: Detection, now: datetime) -> _TrackState:
        suffix = self._label_suffix(self._next_index)
        self._next_index += 1
        track = _TrackState(
            track_id=f'person-{suffix.lower()}',
            track_label=f'person {suffix}',
            first_seen_at=now,
            last_seen_at=now,
            bbox_xyxy=detection.bbox_xyxy,
        )
        self._tracks[track.track_id] = track
        return track

    @staticmethod
    def _apply_track(detection: Detection, track: _TrackState, now: datetime) -> Detection:
        duration = (now - track.first_seen_at).total_seconds()
        return detection.model_copy(
            update={
                'track_id': track.track_id,
                'track_label': track.track_label,
                'first_seen_at': track.first_seen_at,
                'last_seen_at': now,
                'duration_seconds': round(duration, 3),
            },
        )

    @staticmethod
    def _to_person_track(track: _TrackState, now: datetime) -> PersonTrack:
        return PersonTrack(
            track_id=track.track_id,
            track_label=track.track_label,
            first_seen_at=track.first_seen_at,
            last_seen_at=track.last_seen_at,
            duration_seconds=round((now - track.first_seen_at).total_seconds(), 3),
            missed_seconds=round((now - track.last_seen_at).total_seconds(), 3),
        )

    @staticmethod
    def _center_distance(
        first: tuple[float, float, float, float],
        second: tuple[float, float, float, float],
    ) -> float:
        first_x = (first[0] + first[2]) / 2
        first_y = (first[1] + first[3]) / 2
        second_x = (second[0] + second[2]) / 2
        second_y = (second[1] + second[3]) / 2
        return ((first_x - second_x) ** 2 + (first_y - second_y) ** 2) ** 0.5

    @staticmethod
    def _label_suffix(index: int) -> str:
        letters = string.ascii_uppercase
        suffix = ''
        value = index
        while True:
            suffix = letters[value % len(letters)] + suffix
            value = value // len(letters) - 1
            if value < 0:
                return suffix
