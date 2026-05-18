from __future__ import annotations

from pathlib import Path

PLACEHOLDERS = (
    'replace-with-your-wifi-ssid',
    'replace-with-your-wifi-password',
    'http://192.168.0.10:8000/api/v1/frames',
)

REQUIRED_MACROS = (
    'WIFI_SSID',
    'WIFI_PASSWORD',
    'SERVER_URL',
    'CAMERA_ID',
)


def validate_config_header(path: Path) -> None:
    """Validate local firmware config before destructive upload."""
    if not path.is_file():
        msg = f'Missing firmware config: {path}. Copy config.sample.h to config.h and fill local values.'
        raise FileNotFoundError(msg)
    text = path.read_text(encoding='utf-8')
    missing = [macro for macro in REQUIRED_MACROS if macro not in text]
    if missing:
        msg = f'Missing required macros in {path}: {", ".join(missing)}'
        raise ValueError(msg)
    found_placeholders = [value for value in PLACEHOLDERS if value in text]
    if found_placeholders:
        msg = f'Firmware config still contains placeholder values: {", ".join(found_placeholders)}'
        raise ValueError(msg)


def main() -> None:
    validate_config_header(Path('firmware/esp32cam_monitor/include/config.h'))


if __name__ == '__main__':
    main()
