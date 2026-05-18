from __future__ import annotations

from io import BytesIO

from PIL import Image


def build_smoke_jpeg() -> bytes:
    """Build a small valid JPEG for local API smoke tests."""
    image = Image.new('RGB', (64, 64), (255, 255, 255))
    output = BytesIO()
    image.save(output, format='JPEG', quality=90)
    return output.getvalue()


SMOKE_JPEG = build_smoke_jpeg()
