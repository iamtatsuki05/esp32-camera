from pathlib import Path

from project.server.settings import ServerSettings, load_server_settings


def test_load_server_settings_from_toml_and_overrides(tmp_path: Path) -> None:
    config_path = tmp_path / 'server.toml'
    config_path.write_text(
        '\n'.join(
            [
                'host = "0.0.0.0"',
                'port = 9000',
                f'output_dir = "{tmp_path / "out"}"',
                'analyzer = "mock-yolo"',
                'uploader_mode = "dry-run"',
                'default_camera_id = "from-config"',
            ],
        ),
        encoding='utf-8',
    )

    settings = load_server_settings(config_path=config_path, port=9001)

    assert settings == ServerSettings(
        host='0.0.0.0',  # noqa: S104
        port=9001,
        output_dir=tmp_path / 'out',
        analyzer='mock-yolo',
        uploader_mode='dry-run',
        default_camera_id='from-config',
    )
