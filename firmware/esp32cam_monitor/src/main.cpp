#include <Arduino.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include "esp_camera.h"

#if __has_include("config.h")
#include "config.h"
#endif

#ifndef WIFI_SSID
#define WIFI_SSID "replace-with-your-wifi-ssid"
#endif
#ifndef WIFI_PASSWORD
#define WIFI_PASSWORD "replace-with-your-wifi-password"
#endif
#ifndef SERVER_URL
#define SERVER_URL "http://192.168.0.10:8000/api/v1/frames"
#endif
#ifndef CAMERA_ID
#define CAMERA_ID "esp32-cam-01"
#endif
#ifndef CAPTURE_INTERVAL_MS
#define CAPTURE_INTERVAL_MS 10000
#endif

namespace {

bool camera_ready = false;

constexpr int PWDN_GPIO_NUM = 32;
constexpr int RESET_GPIO_NUM = -1;
constexpr int XCLK_GPIO_NUM = 0;
constexpr int SIOD_GPIO_NUM = 26;
constexpr int SIOC_GPIO_NUM = 27;
constexpr int Y9_GPIO_NUM = 35;
constexpr int Y8_GPIO_NUM = 34;
constexpr int Y7_GPIO_NUM = 39;
constexpr int Y6_GPIO_NUM = 36;
constexpr int Y5_GPIO_NUM = 21;
constexpr int Y4_GPIO_NUM = 19;
constexpr int Y3_GPIO_NUM = 18;
constexpr int Y2_GPIO_NUM = 5;
constexpr int VSYNC_GPIO_NUM = 25;
constexpr int HREF_GPIO_NUM = 23;
constexpr int PCLK_GPIO_NUM = 22;

bool connect_wifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting Wi-Fi");
  for (int retry = 0; retry < 40 && WiFi.status() != WL_CONNECTED; retry++) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi connection failed");
    return false;
  }
  Serial.print("Wi-Fi connected: ");
  Serial.println(WiFi.localIP());
  return true;
}

bool setup_camera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 12;
  config.fb_count = 1;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;

  const esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    return false;
  }
  Serial.println("Camera initialized");
  return true;
}

void post_frame() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (fb == nullptr) {
    Serial.println("Camera capture failed");
    return;
  }

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("X-Camera-Id", CAMERA_ID);
  const int code = http.POST(fb->buf, fb->len);
  Serial.printf("POST %s -> %d, bytes=%u\n", SERVER_URL, code, fb->len);
  if (code > 0) {
    Serial.println(http.getString());
  }
  http.end();
  esp_camera_fb_return(fb);
}

}  // namespace

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("ESP32-CAM monitor booting");
  if (!connect_wifi()) {
    return;
  }
  camera_ready = setup_camera();
}

void loop() {
  if (!camera_ready) {
    Serial.println("Camera is not ready; retrying initialization");
    camera_ready = setup_camera();
    delay(CAPTURE_INTERVAL_MS);
    return;
  }
  if (WiFi.status() != WL_CONNECTED) {
    connect_wifi();
  }
  post_frame();
  delay(CAPTURE_INTERVAL_MS);
}
