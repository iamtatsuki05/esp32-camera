# ESP32-CAM firmware

この雛形は AI Thinker ESP32-CAM（OV2640）を前提にしています。
別ボードの場合は `platformio.ini` と `src/main.cpp` のピン定義を変更してください。

## 初期設定

```sh
cp firmware/esp32cam_monitor/include/config.sample.h firmware/esp32cam_monitor/include/config.h
```

`config.h` に Wi-Fi SSID、Wi-Fi password、PC 側サーバー URL、camera ID、撮影 JPEG quality を設定します。
`config.h` は `.gitignore` 済みです。
repo root の `make esp32-upload` は、placeholder が残っている `config.h` では停止します。

`CAMERA_JPEG_QUALITY` は ESP32-CAM 側の撮影品質です。数値が小さいほど高画質・大きい payload になります。サーバー保存時の再エンコード品質は root の `config/server*.toml` の `save_jpeg_quality` で設定します。

## ビルド

```sh
cd firmware/esp32cam_monitor
uv tool run --with pip platformio run
```

## 書き込み

書き込みは既存 firmware を上書きします。対象ポートを確認してから実行してください。

```sh
cd firmware/esp32cam_monitor
uv tool run --with pip platformio run -t upload --upload-port /dev/cu.usbserial-1440
```

## シリアルモニタ

```sh
cd firmware/esp32cam_monitor
uv tool run --with pip platformio device monitor -p /dev/cu.usbserial-1440 -b 115200
```

起動後、Wi-Fi 接続、camera init、`POST ... -> 201` が出れば PC 側サーバーへ送信できています。
