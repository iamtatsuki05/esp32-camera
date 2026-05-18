from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, Response, status

from project.server.analyzers import create_analyzer
from project.server.image_validation import validate_image_bytes
from project.server.models import AnalysisResult, FrameInput
from project.server.pipeline import AnalysisPipeline
from project.server.settings import ServerSettings
from project.server.storage import LocalFrameStorage
from project.server.uploaders import create_uploader


def create_app(settings: ServerSettings | None = None) -> FastAPI:
    """Create the FastAPI app used by local development and ESP32-CAM."""
    resolved_settings = settings or ServerSettings()
    pipeline = AnalysisPipeline(
        analyzer=create_analyzer(
            resolved_settings.analyzer,
            yolo_model_path=resolved_settings.yolo_model_path,
            yolo_confidence_threshold=resolved_settings.yolo_confidence_threshold,
        ),
        storage=LocalFrameStorage(
            output_dir=resolved_settings.output_dir,
            save_jpeg_quality=resolved_settings.save_jpeg_quality,
        ),
        uploader=create_uploader(resolved_settings.uploader_mode, resolved_settings.output_dir),
    )
    app = FastAPI(title='ESP32 Camera Monitor', version='0.1.0')
    app.state.settings = resolved_settings
    app.state.pipeline = pipeline

    @app.get('/health')
    def health() -> dict[str, str]:
        return {
            'status': 'ok',
            'analyzer': resolved_settings.analyzer,
            'uploader_mode': resolved_settings.uploader_mode,
            'yolo_model_path': resolved_settings.yolo_model_path,
        }

    @app.post('/api/v1/frames', response_model=AnalysisResult, status_code=status.HTTP_201_CREATED)
    async def ingest_frame(request: Request, response: Response) -> AnalysisResult:
        image_bytes = await request.body()
        if not image_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Frame body is empty.')
        content_type = request.headers.get('content-type', 'image/jpeg')
        try:
            content_type = validate_image_bytes(image_bytes, content_type)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)) from exc
        camera_id = request.headers.get('x-camera-id', resolved_settings.default_camera_id)
        frame = FrameInput(image_bytes=image_bytes, content_type=content_type, camera_id=camera_id)
        result = app.state.pipeline.process(frame)
        response.headers['x-event-id'] = result.event_id
        return result

    return app


app = create_app()
