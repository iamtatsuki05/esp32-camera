import pytest

from project.server.image_validation import validate_image_bytes
from project.server.sample_images import SMOKE_JPEG


def test_validate_image_bytes_accepts_jpeg_smoke_image() -> None:
    assert validate_image_bytes(SMOKE_JPEG, 'image/jpeg') == 'image/jpeg'


def test_validate_image_bytes_rejects_fake_jpeg_text() -> None:
    with pytest.raises(ValueError, match='not a supported'):
        validate_image_bytes(b'smoke-frame', 'image/jpeg')


def test_validate_image_bytes_rejects_corrupt_jpeg_payload() -> None:
    with pytest.raises(ValueError, match='not a valid'):
        validate_image_bytes(b'\xff\xd8\xffnot-a-real-jpeg', 'image/jpeg')


def test_validate_image_bytes_rejects_content_type_mismatch() -> None:
    with pytest.raises(ValueError, match='mismatch'):
        validate_image_bytes(SMOKE_JPEG, 'image/png')
