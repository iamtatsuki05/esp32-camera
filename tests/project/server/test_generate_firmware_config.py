import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parents[3] / 'scripts' / 'generate_firmware_config.py'
spec = importlib.util.spec_from_file_location('generate_firmware_config', SCRIPT_PATH)
assert spec is not None
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

load_firmware_env = module.load_firmware_env
render_config_header = module.render_config_header
write_config_header = module.write_config_header


def test_load_firmware_env_rejects_missing_env(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_firmware_env(tmp_path / '.env')


def test_load_firmware_env_rejects_placeholder_values(tmp_path: Path) -> None:
    env_path = tmp_path / '.env'
    env_path.write_text(
        """ESP32_WIFI_SSID=replace-with-your-wifi-ssid
ESP32_WIFI_PASSWORD=secret
ESP32_CAMERA_SERVER_URL=http://10.0.0.1:8000/api/v1/frames
ESP32_CAMERA_ID=esp32-cam-01
""",
        encoding='utf-8',
    )

    with pytest.raises(ValueError, match='Placeholder'):
        load_firmware_env(env_path)


def test_render_config_header_escapes_c_strings() -> None:
    header = render_config_header(
        {
            'ESP32_WIFI_SSID': 'lab"wifi',
            'ESP32_WIFI_PASSWORD': 'pa\\ss',
            'ESP32_CAMERA_SERVER_URL': 'http://10.0.0.1:8000/api/v1/frames',
            'ESP32_CAMERA_ID': 'esp32-cam-01',
        },
    )

    assert '#define WIFI_SSID "lab\\"wifi"' in header
    assert '#define WIFI_PASSWORD "pa\\\\ss"' in header
    assert '#define CAPTURE_INTERVAL_MS 10000' in header
    assert '#define CAMERA_JPEG_QUALITY 12' in header


def test_write_config_header_from_env(tmp_path: Path) -> None:
    env_path = tmp_path / '.env'
    config_path = tmp_path / 'config.h'
    env_path.write_text(
        """ESP32_WIFI_SSID=lab-wifi
ESP32_WIFI_PASSWORD=secret
ESP32_CAMERA_SERVER_URL=http://10.0.0.1:8000/api/v1/frames
ESP32_CAMERA_ID=esp32-cam-01
ESP32_CAPTURE_INTERVAL_MS=5000
ESP32_CAMERA_JPEG_QUALITY=10
""",
        encoding='utf-8',
    )

    write_config_header(env_path=env_path, config_path=config_path)

    header = config_path.read_text(encoding='utf-8')
    assert '#define WIFI_SSID "lab-wifi"' in header
    assert '#define SERVER_URL "http://10.0.0.1:8000/api/v1/frames"' in header
    assert '#define CAPTURE_INTERVAL_MS 5000' in header
    assert '#define CAMERA_JPEG_QUALITY 10' in header
