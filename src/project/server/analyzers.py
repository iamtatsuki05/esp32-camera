from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from typing import Any, Protocol

from project.server.models import Detection, FrameInput

ORIG_SHAPE_MIN_LEN = 2
XYXY_LEN = 4


class FrameAnalyzer(Protocol):
    """Interface for YOLO-compatible frame analyzers."""

    name: str

    def analyze(self, frame: FrameInput) -> list[Detection]:
        """Analyze one frame and return normalized detections."""
        ...


class MockYoloAnalyzer:
    """Deterministic smoke-test analyzer used when no heavy model is installed."""

    name = 'mock-yolo'

    def __init__(self, detections_per_frame: int = 1, label: str = 'mock-object') -> None:
        self.detections_per_frame = detections_per_frame
        self.label = label

    def analyze(self, frame: FrameInput) -> list[Detection]:
        digest = hashlib.sha256(frame.image_bytes).digest()
        detections = []
        for index in range(self.detections_per_frame):
            confidence = 0.5 + (digest[index % len(digest)] / 255.0) * 0.4
            offset = index * 0.05
            detections.append(
                Detection(
                    label=self.label,
                    confidence=round(confidence, 4),
                    bbox_xyxy=(0.1 + offset, 0.1, 0.3 + offset, 0.5),
                    class_id=0 if self.label == 'person' else None,
                ),
            )
        return detections


class UltralyticsYoloAnalyzer:
    """YOLO analyzer backed by ultralytics when that package is installed."""

    name = 'ultralytics-yolo'

    def __init__(
        self,
        model_path: str = 'yolov8n.pt',
        *,
        model: Any | None = None,  # noqa: ANN401
        confidence_threshold: float = 0.25,
        target_labels: tuple[str, ...] = ('person',),
    ) -> None:
        self.model_path = model_path
        self.model = model
        self.confidence_threshold = confidence_threshold
        self.target_labels = set(target_labels)

    def analyze(self, frame: FrameInput) -> list[Detection]:
        model = self._load_model()
        suffix = '.png' if frame.content_type.startswith('image/png') else '.jpg'
        with tempfile.NamedTemporaryFile(suffix=suffix) as image_file:
            image_file.write(frame.image_bytes)
            image_file.flush()
            results = model.predict(str(Path(image_file.name)), conf=self.confidence_threshold, verbose=False)
        return self._detections_from_results(results)

    def _load_model(self) -> Any:  # noqa: ANN401
        if self.model is None:
            try:
                from ultralytics import YOLO  # noqa: PLC0415
            except ImportError as exc:
                msg = (
                    'ultralytics is required for analyzer=ultralytics-yolo. '
                    'Install it explicitly, for example: uv pip install ultralytics'
                )
                raise RuntimeError(msg) from exc
            self.model = YOLO(self.model_path)
        return self.model

    def _detections_from_results(self, results: Any) -> list[Detection]:  # noqa: ANN401
        detections: list[Detection] = []
        for result in results:
            names = getattr(result, 'names', {})
            for box in getattr(result, 'boxes', []):
                class_id = int(box.cls[0].item())
                label = str(names.get(class_id, class_id))
                confidence = float(box.conf[0].item())
                if label not in self.target_labels or confidence < self.confidence_threshold:
                    continue
                raw_xyxy = [float(value) for value in box.xyxy[0].tolist()]
                if len(raw_xyxy) != XYXY_LEN:
                    continue
                xyxy = self._normalize_xyxy(
                    (raw_xyxy[0], raw_xyxy[1], raw_xyxy[2], raw_xyxy[3]), getattr(result, 'orig_shape', None)
                )
                detections.append(
                    Detection(
                        label=label,
                        confidence=round(confidence, 4),
                        bbox_xyxy=xyxy,  # type: ignore[arg-type]
                        class_id=class_id,
                    ),
                )
        return detections

    @staticmethod
    def _normalize_xyxy(
        xyxy: tuple[float, float, float, float],
        orig_shape: object,
    ) -> tuple[float, float, float, float]:
        if not isinstance(orig_shape, tuple) or len(orig_shape) < ORIG_SHAPE_MIN_LEN:
            return xyxy
        height = float(orig_shape[0])
        width = float(orig_shape[1])
        if height <= 0 or width <= 0:
            return xyxy
        return (
            round(xyxy[0] / width, 6),
            round(xyxy[1] / height, 6),
            round(xyxy[2] / width, 6),
            round(xyxy[3] / height, 6),
        )


def create_analyzer(
    name: str,
    *,
    yolo_model_path: str = 'yolov8n.pt',
    yolo_confidence_threshold: float = 0.25,
) -> FrameAnalyzer:
    """Create an analyzer by name."""
    if name == 'mock-yolo':
        return MockYoloAnalyzer()
    if name == 'ultralytics-yolo':
        return UltralyticsYoloAnalyzer(
            model_path=yolo_model_path,
            confidence_threshold=yolo_confidence_threshold,
        )
    msg = f'Unsupported analyzer: {name}'
    raise ValueError(msg)
