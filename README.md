# ESP32 Camera Monitor

ESP32-CAM を常駐監視カメラとして動かし、PC 側の Python サーバーで画像受信、YOLO 互換の解析、ローカル保存、アップロード dry-run まで確認するための開発用コードベースです。

現時点では AI Thinker ESP32-CAM（OV2640）を前提にしています。実機ボードが別種の場合は未検証です。

## 構成

- `firmware/esp32cam_monitor/`: ESP32-CAM firmware。PlatformIO + Arduino framework。
- `src/project/server/`: PC 側 FastAPI サーバー、解析 pipeline、保存、dry-run upload。
- `scripts/list_serial_ports.py`: macOS/Linux のシリアルポート候補確認。
- `scripts/post_sample_frame.py`: 起動済みサーバーへサンプル frame を POST。
- `config/server.sample.toml`: サーバー設定例。
- `env.sample`: ESP32 とサーバー設定の環境変数例。秘密値は入れないでください。
- `data/outputs/`: 画像、解析 JSON、dry-run upload payload の出力先。

## 必要環境

- Python 3.13
- `uv`
- ESP32 firmware を扱う場合は PlatformIO CLI（`pio`）
- AI Thinker ESP32-CAM、USB-serial adapter、書き込み用配線

PlatformIO が未導入の場合:

```sh
uv tool install --with pip platformio
```

一時実行だけなら `uv tool run --with pip platformio --version` でも確認できます。`--with pip` は PlatformIO が `tool-esptoolpy` の追加依存を展開するために必要でした。

## 初回セットアップ

```sh
cd /Users/tatsuki/src/esp32-camera
uv sync
cp env.sample .env
```

`.env` はローカルメモ用です。現状のサーバー CLI は引数で設定します。Wi-Fi password などの秘密値は repo に commit しないでください。

## ローカル検証

テスト:

```sh
uv run pytest tests/
```

lint/type check:

```sh
uv run ruff check src/ tests/ scripts/
uv run ruff format --check src/ tests/ scripts/
uv run mypy src/ tests/ scripts/
```

サーバー起動:

```sh
uv run python -m project.server.cli serve --host 127.0.0.1 --port 8000 --output-dir data/outputs
```

設定ファイルを使う場合:

```sh
uv run python -m project.server.cli serve --config-file config/server.sample.toml
```

別 terminal で health check:

```sh
curl http://127.0.0.1:8000/health
```

サンプル frame POST:

```sh
uv run python scripts/post_sample_frame.py
```

保存先:

- `data/outputs/videos/*.avi`
- `data/outputs/results/*.json`
- `data/outputs/uploads/dry-run/*.json`

サーバーは受信 frame を個別画像として保存せず、camera ID ごとの動画に追記します。解析 JSON には `video_path` と `video_frame_index` が残ります。

動画へ書き込む前の JPEG 再エンコード品質は `save_jpeg_quality` で設定できます。

```toml
save_jpeg_quality = 85
```

`null` または項目なしなら、受信した JPEG bytes をそのまま動画 frame に変換します。`1` から `95` を指定すると、動画へ書き込む前に JPEG を再エンコードします。数値が大きいほど高画質・大きいファイルになります。

動画 FPS は `video_fps` で設定します。

```toml
video_fps = 2.0
```

既定は `mock-yolo` です。実 YOLO を使う場合は、追加で `ultralytics` を入れ、`analyzer = "ultralytics-yolo"` に切り替えます。

```sh
uv add ultralytics
```

この repo では `config/server.yolo.sample.toml` を用意しています。

```sh
uv run python -m project.server.cli serve --config-file config/server.yolo.sample.toml
```

`yolov8n.pt` は初回実行時にモデル取得が発生する場合があります。ネットワークやライセンス確認が必要な環境では、事前に確認した model path を指定してください。

## ESP32 接続確認

ESP32 を PC に接続してから、ポート候補を確認します。

```sh
make esp32-ports
```

今回の環境では `/dev/cu.usbserial-1440` が候補として見えました。ただし実際に ESP32-CAM かどうか、配線、boot mode は未検証です。

macOS で手動確認する場合:

```sh
ls /dev/cu.* /dev/tty.* 2>/dev/null
```

## Firmware 設定

```sh
cp firmware/esp32cam_monitor/include/config.sample.h firmware/esp32cam_monitor/include/config.h
```

手で `config.h` を編集する代わりに、`.env` から生成できます。

```sh
cp env.sample .env
$EDITOR .env
make esp32-config
```

`.env` で使う主な項目:

- `ESP32_WIFI_SSID`
- `ESP32_WIFI_PASSWORD`
- `ESP32_CAMERA_SERVER_URL`: 例 `http://192.168.0.10:8000/api/v1/frames`
- `ESP32_CAMERA_ID`
- `ESP32_CAPTURE_INTERVAL_MS`
- `ESP32_CAMERA_JPEG_QUALITY`: ESP32 側の撮影 JPEG 品質。ESP32-CAM では数値が小さいほど高画質・大きい payload です。

PC 側サーバーを ESP32 から到達できる IP で起動してください。

```sh
uv run python -m project.server.cli serve --host 0.0.0.0 --port 8000 --output-dir data/outputs
```

この Mac では検証時点で LAN IP として `163.221.126.95` が見えていました。ESP32 側の `SERVER_URL` は同じネットワークから到達できる IP に合わせて、例えば `http://163.221.126.95:8000/api/v1/frames` のように設定します。

## Firmware ビルド

```sh
make esp32-build
```

同等の直接コマンド:

```sh
cd firmware/esp32cam_monitor
uv tool run --with pip platformio run
```

## Firmware 書き込み

書き込みは ESP32 の既存 firmware を上書きします。対象ポート、ボード、配線、boot mode を確認してから実行してください。
`make esp32-upload` は `.env` から `config.h` を生成し、sample の placeholder が残っていない場合だけ進みます。

```sh
make esp32-upload PORT=/dev/cu.usbserial-1440
```

同等の直接コマンド:

```sh
cd firmware/esp32cam_monitor
uv tool run --with pip platformio run -t upload --upload-port /dev/cu.usbserial-1440
```

## 実行確認

1. PC 側サーバーを起動します。

```sh
uv run python -m project.server.cli serve --host 0.0.0.0 --port 8000 --output-dir data/outputs
```

2. ESP32-CAM のシリアルログを確認します。

```sh
make esp32-monitor PORT=/dev/cu.usbserial-1440
```

3. ESP32 ログで以下を確認します。

- Wi-Fi connected
- Camera initialized
- `POST ... -> 201`

4. PC 側で保存結果を確認します。

```sh
find data/outputs -type f | sort
```

動画だけを見る場合:

```sh
find data/outputs/videos -type f | sort
```

## API

Health:

```sh
curl http://127.0.0.1:8000/health
```

Frame ingest:

```sh
curl -X POST \
  -H 'Content-Type: image/jpeg' \
  -H 'X-Camera-Id: local-curl' \
  --data-binary @README.md \
  http://127.0.0.1:8000/api/v1/frames
```

`README.md` を画像として扱うのは smoke test 用です。実運用では JPEG bytes を送ります。

レスポンスには、検出された人物数とサーバー起動中の人物 track が含まれます。

- `person_count`: その frame で検出された人物数。
- `active_person_count`: tracking 上まだ認識中の人物数。
- `detections[].track_label`: `person A`, `person B`, `person C` のような一時ラベル。
- `detections[].duration_seconds`: その人物が最初に認識されてから現在 frame までの秒数。
- `active_tracks`: 現在認識中または猶予時間内の人物。
- `ended_tracks`: 今回の frame で認識終了扱いになった人物。
- `video_path`: frame が追記された動画ファイル。
- `video_frame_index`: その動画内の frame index。

## アップロード方針

外部サービスへの実アップロードは未実装です。既定では `dry-run` として、送信予定 payload を `data/outputs/uploads/dry-run/` に保存します。

実アップロードを追加する場合は `src/project/server/uploaders.py` に `ResultUploader` 実装を追加し、明示的な設定がある場合だけ有効にしてください。認証情報や公開 URL は repo に保存しないでください。

## トラブルシュート

- `pio: command not found`: `uv tool install --with pip platformio` を実行します。
- ポートが見えない: USB ケーブル、USB-serial adapter、ドライバ、電源を確認します。
- 書き込みに失敗する: IO0/GND の boot mode、5V/GND、TX/RX の交差、リセット操作を確認します。
- ESP32 からサーバーに届かない: `host 0.0.0.0` で起動し、`SERVER_URL` に PC の LAN IP を使います。
- `POST ... -> -1`: Wi-Fi、PC firewall、URL、同一ネットワークを確認します。
- 解析が mock のまま: `config/server.sample.toml` の `analyzer` を `ultralytics-yolo` に変え、`ultralytics` と model path を用意してください。

## 未検証事項

- 実機への firmware 書き込みとシリアル監視。
- `/dev/cu.usbserial-1440` が対象 ESP32-CAM であること。
- AI Thinker 以外の ESP32-CAM ボード。
- 実 YOLO モデルによる推論は `ultralytics` assets の `bus.jpg` で確認済みです。ESP32 実機画像での推論は Wi-Fi 設定後に確認が必要です。
- 外部サービスへの実アップロード。
