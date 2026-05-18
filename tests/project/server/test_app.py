from pathlib import Path

from fastapi.testclient import TestClient

from project.server.app import create_app
from project.server.settings import ServerSettings


def test_frame_endpoint_accepts_raw_image_and_returns_saved_paths(tmp_path: Path) -> None:
    app = create_app(ServerSettings(output_dir=tmp_path))
    client = TestClient(app)

    response = client.post(
        '/api/v1/frames',
        content=b'jpeg-bytes',
        headers={
            'content-type': 'image/jpeg',
            'x-camera-id': 'esp32-test',
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload['camera_id'] == 'esp32-test'
    assert payload['analyzer'] == 'mock-yolo'
    assert payload['upload']['status'] == 'dry-run'
    assert payload['image_path'].endswith('.jpg')
    assert Path(payload['image_path']).is_file()
    assert Path(payload['result_path']).is_file()


def test_health_endpoint_reports_dry_run_defaults(tmp_path: Path) -> None:
    app = create_app(ServerSettings(output_dir=tmp_path))
    client = TestClient(app)

    response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {
        'status': 'ok',
        'analyzer': 'mock-yolo',
        'uploader_mode': 'dry-run',
        'yolo_model_path': 'yolov8n.pt',
    }
