from __future__ import annotations

import sys
from pathlib import Path

from dotenv import dotenv_values

CONFIG_PATH = Path('firmware/esp32cam_monitor/include/config.h')
ENV_PATH = Path('.env')

REQUIRED_ENV_KEYS = (
    'ESP32_WIFI_SSID',
    'ESP32_WIFI_PASSWORD',
    'ESP32_CAMERA_SERVER_URL',
    'ESP32_CAMERA_ID',
)


def _c_string(value: str) -> str:
    return value.replace('\\', '\\\\').replace('"', '\\"')


def load_firmware_env(env_path: Path = ENV_PATH) -> dict[str, str]:
    """Load ESP32 firmware settings from .env without printing secret values."""
    if not env_path.is_file():
        msg = f'Missing {env_path}. Copy env.sample to .env and fill ESP32_* values.'
        raise FileNotFoundError(msg)
    values = {key: value for key, value in dotenv_values(env_path).items() if value is not None}
    missing = [key for key in REQUIRED_ENV_KEYS if not values.get(key)]
    if missing:
        msg = f'Missing required keys in {env_path}: {", ".join(missing)}'
        raise ValueError(msg)
    placeholders = [
        key
        for key in REQUIRED_ENV_KEYS
        if values[key].startswith('replace-with-') or values[key] == 'http://192.168.0.10:8000/api/v1/frames'
    ]
    if placeholders:
        msg = f'Placeholder values remain in {env_path}: {", ".join(placeholders)}'
        raise ValueError(msg)
    return values


def render_config_header(values: dict[str, str]) -> str:
    """Render config.h from validated environment values."""
    capture_interval_ms = values.get('ESP32_CAPTURE_INTERVAL_MS', '10000')
    camera_jpeg_quality = values.get('ESP32_CAMERA_JPEG_QUALITY', '12')
    return (
        '#pragma once\n'
        '\n'
        '// Generated from .env by scripts/generate_firmware_config.py.\n'
        '// Do not commit this file.\n'
        '\n'
        f'#define WIFI_SSID "{_c_string(values["ESP32_WIFI_SSID"])}"\n'
        f'#define WIFI_PASSWORD "{_c_string(values["ESP32_WIFI_PASSWORD"])}"\n'
        f'#define SERVER_URL "{_c_string(values["ESP32_CAMERA_SERVER_URL"])}"\n'
        f'#define CAMERA_ID "{_c_string(values["ESP32_CAMERA_ID"])}"\n'
        f'#define CAPTURE_INTERVAL_MS {capture_interval_ms}\n'
        f'#define CAMERA_JPEG_QUALITY {camera_jpeg_quality}\n'
    )


def write_config_header(env_path: Path = ENV_PATH, config_path: Path = CONFIG_PATH) -> Path:
    """Generate firmware config.h from .env."""
    values = load_firmware_env(env_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(render_config_header(values), encoding='utf-8')
    return config_path


def main() -> None:
    path = write_config_header()
    sys.stdout.write(f'Generated {path} from .env\n')


if __name__ == '__main__':
    main()
