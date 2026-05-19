.PHONY: help setup test lint format server smoke-api smoke-file esp32-ports esp32-config esp32-build esp32-upload esp32-monitor

PORT ?=
PIO ?= uv tool run --with pip platformio

help:
	@printf '%s\n' \
		'Targets:' \
		'  setup          uv sync' \
		'  test           run pytest' \
		'  lint           run ruff/mypy checks' \
		'  format         run ruff format' \
		'  server         start FastAPI server on 127.0.0.1:8000' \
		'  smoke-api      post a sample frame to the running server' \
		'  smoke-file     analyze README.md bytes as a local smoke input' \
		'  esp32-ports    list serial port candidates' \
		'  esp32-config   generate firmware config.h from .env' \
		'  esp32-build    build ESP32 firmware with PlatformIO' \
		'  esp32-upload   upload firmware; requires PORT=/dev/cu.xxx' \
		'  esp32-monitor  serial monitor; requires PORT=/dev/cu.xxx'

setup:
	uv sync

test:
	uv run pytest tests/

lint:
	uv run ruff check src/ tests/ scripts/
	uv run ruff format --check src/ tests/ scripts/
	uv run mypy src/ tests/ scripts/

format:
	uv run ruff format src/ tests/ scripts/

server:
	uv run python -m project.server.cli serve --host 127.0.0.1 --port 8000 --output-dir data/outputs

smoke-api:
	uv run python scripts/post_sample_frame.py

smoke-file:
	uv run python -m project.server.cli analyze-file README.md --output-dir data/outputs --camera-id local-file

esp32-ports:
	uv run python scripts/list_serial_ports.py

esp32-config:
	uv run python scripts/generate_firmware_config.py

esp32-build:
	$(PIO) run -d firmware/esp32cam_monitor

esp32-upload:
	@test -n "$(PORT)" || (echo 'Set PORT=/dev/cu.xxx before upload.' >&2; exit 2)
	uv run python scripts/generate_firmware_config.py
	uv run python scripts/check_firmware_config.py
	$(PIO) run -d firmware/esp32cam_monitor -t upload --upload-port "$(PORT)"

esp32-monitor:
	@test -n "$(PORT)" || (echo 'Set PORT=/dev/cu.xxx before monitor.' >&2; exit 2)
	cd firmware/esp32cam_monitor && $(PIO) device monitor -p "$(PORT)" -b 115200
