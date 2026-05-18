from __future__ import annotations

from pathlib import Path  # noqa: TC003

import typer
import uvicorn

from project.server.analyzers import create_analyzer
from project.server.app import create_app
from project.server.models import FrameInput
from project.server.pipeline import AnalysisPipeline
from project.server.settings import load_server_settings
from project.server.storage import LocalFrameStorage
from project.server.uploaders import create_uploader

cli = typer.Typer(help='ESP32-CAM monitoring server utilities.')


@cli.command()
def serve(  # noqa: PLR0913
    config_file: Path | None = None,
    host: str | None = None,
    port: int | None = None,
    output_dir: Path | None = None,
    analyzer: str | None = None,
    yolo_model_path: str | None = None,
    yolo_confidence_threshold: float | None = None,
    uploader_mode: str | None = None,
    default_camera_id: str | None = None,
) -> None:
    """Run the local FastAPI server."""
    settings = load_server_settings(
        config_path=config_file,
        host=host,
        port=port,
        output_dir=output_dir,
        analyzer=analyzer,
        yolo_model_path=yolo_model_path,
        yolo_confidence_threshold=yolo_confidence_threshold,
        uploader_mode=uploader_mode,
        default_camera_id=default_camera_id,
    )
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port)


@cli.command()
def analyze_file(
    image_path: Path,
    config_file: Path | None = None,
    output_dir: Path | None = None,
    camera_id: str = 'local-file',
) -> None:
    """Run the same pipeline against a local image file."""
    settings = load_server_settings(config_path=config_file, output_dir=output_dir)
    pipeline = AnalysisPipeline(
        analyzer=create_analyzer(
            settings.analyzer,
            yolo_model_path=settings.yolo_model_path,
            yolo_confidence_threshold=settings.yolo_confidence_threshold,
        ),
        storage=LocalFrameStorage(settings.output_dir),
        uploader=create_uploader(settings.uploader_mode, settings.output_dir),
    )
    result = pipeline.process(
        FrameInput(
            image_bytes=image_path.read_bytes(),
            content_type='image/jpeg',
            camera_id=camera_id,
        ),
    )
    typer.echo(result.model_dump_json(indent=2))


if __name__ == '__main__':
    cli()
