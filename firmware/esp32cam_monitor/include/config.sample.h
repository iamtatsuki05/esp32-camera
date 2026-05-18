#pragma once

// Copy this file to include/config.h and fill local values.
// Do not commit include/config.h.

#define WIFI_SSID "replace-with-your-wifi-ssid"
#define WIFI_PASSWORD "replace-with-your-wifi-password"
#define SERVER_URL "http://192.168.0.10:8000/api/v1/frames"
#define CAMERA_ID "esp32-cam-01"

// Keep this interval conservative while testing on USB power.
#define CAPTURE_INTERVAL_MS 10000

