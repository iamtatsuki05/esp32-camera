import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT_PATH = Path(__file__).parents[3] / 'scripts' / 'check_firmware_config.py'
spec = importlib.util.spec_from_file_location('check_firmware_config', SCRIPT_PATH)
assert spec is not None
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
assert isinstance(module, ModuleType)
validate_config_header = module.validate_config_header


def test_validate_config_header_rejects_missing_config(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        validate_config_header(tmp_path / 'config.h')


def test_validate_config_header_rejects_placeholder_values(tmp_path: Path) -> None:
    config = tmp_path / 'config.h'
    config.write_text(
        """#define WIFI_SSID "replace-with-your-wifi-ssid"
#define WIFI_PASSWORD "local-password"
#define SERVER_URL "http://192.168.0.99:8000/api/v1/frames"
#define CAMERA_ID "esp32-cam-01"
""",
        encoding='utf-8',
    )

    with pytest.raises(ValueError, match='placeholder'):
        validate_config_header(config)


def test_validate_config_header_accepts_local_values(tmp_path: Path) -> None:
    config = tmp_path / 'config.h'
    config.write_text(
        """#define WIFI_SSID "local-wifi"
#define WIFI_PASSWORD "local-password"
#define SERVER_URL "http://192.168.0.99:8000/api/v1/frames"
#define CAMERA_ID "esp32-cam-01"
""",
        encoding='utf-8',
    )

    validate_config_header(config)
