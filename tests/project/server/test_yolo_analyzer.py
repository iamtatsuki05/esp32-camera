from typing import ClassVar

from project.server.analyzers import UltralyticsYoloAnalyzer
from project.server.models import FrameInput


class _FakeBox:
    def __init__(self, cls: int, confidence: float, xyxy: tuple[float, float, float, float]) -> None:
        self.cls = [_Scalar(cls)]
        self.conf = [_Scalar(confidence)]
        self.xyxy = [_Array(xyxy)]


class _Scalar:
    def __init__(self, value: float) -> None:
        self._value = value

    def item(self) -> float:
        return self._value


class _Array:
    def __init__(self, value: tuple[float, float, float, float]) -> None:
        self._value = value

    def tolist(self) -> list[float]:
        return list(self._value)


class _FakeResult:
    names: ClassVar[dict[int, str]] = {0: 'person', 1: 'car'}
    orig_shape: ClassVar[tuple[int, int]] = (100, 200)
    boxes: ClassVar[list[_FakeBox]] = [
        _FakeBox(0, 0.91, (20.0, 10.0, 60.0, 50.0)),
        _FakeBox(1, 0.88, (5.0, 6.0, 7.0, 8.0)),
    ]


class _FakeModel:
    def predict(self, *_args: object, **_kwargs: object) -> list[_FakeResult]:
        return [_FakeResult()]


def test_ultralytics_yolo_analyzer_maps_person_detections_only() -> None:
    analyzer = UltralyticsYoloAnalyzer(model=_FakeModel())

    detections = analyzer.analyze(
        FrameInput(
            image_bytes=b'fake-image',
            content_type='image/jpeg',
            camera_id='test',
        ),
    )

    assert len(detections) == 1
    assert detections[0].label == 'person'
    assert detections[0].class_id == 0
    assert detections[0].confidence == 0.91
    assert detections[0].bbox_xyxy == (0.1, 0.1, 0.3, 0.5)
