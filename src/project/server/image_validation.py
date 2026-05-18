from __future__ import annotations


def detect_image_content_type(image_bytes: bytes) -> str | None:
    """Detect supported image content type from file magic bytes."""
    if image_bytes.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    return None


def normalize_image_content_type(content_type: str) -> str:
    """Normalize supported image content types."""
    normalized = content_type.split(';', maxsplit=1)[0].strip().lower()
    if normalized == 'image/jpg':
        return 'image/jpeg'
    return normalized


def validate_image_bytes(image_bytes: bytes, content_type: str) -> str:
    """Return normalized content type if bytes and declared content type match."""
    declared = normalize_image_content_type(content_type)
    detected = detect_image_content_type(image_bytes)
    if detected is None:
        msg = 'Frame body is not a supported JPEG or PNG image.'
        raise ValueError(msg)
    if declared not in {'image/jpeg', 'image/png'}:
        msg = f'Unsupported image content type: {content_type}'
        raise ValueError(msg)
    if detected != declared:
        msg = f'Image content type mismatch: declared {declared}, detected {detected}'
        raise ValueError(msg)
    return detected
