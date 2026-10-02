#include "DEV_Config.h"
#include "LCD_1in28.h"
#include "ConnectorAnimation.h"

static UWORD frame[240 * 240];
UWORD *BlackImage = frame;
static uint8_t state = 0;
static uint16_t frameIndex = 0;
static uint32_t nextFrameAt = 0;
static uint32_t displayedFrames = 0;
static uint32_t lastReport = 0;

// Each record skips unchanged pixels or supplies literal big-endian RGB565.
bool applyFrame(uint8_t which, uint16_t index) {
  if (index == 0) memset(frame, 0, sizeof(frame));
  const uint32_t begin = animationOffsets[which][index];
  const uint32_t end = animationOffsets[which][index + 1];
  uint32_t pos = begin, pixel = 0;
  uint8_t *dst = reinterpret_cast<uint8_t *>(frame);
  while (pos < end) {
    if (pos + 2 > end) return false;
    const uint16_t op = animationData[pos] | (animationData[pos + 1] << 8);
    pos += 2;
    const uint16_t count = op & 0x7fff;
    if (!count || pixel + count > 240 * 240) return false;
    if (op & 0x8000) {
      const uint32_t bytes = count * 2;
      if (pos + bytes > end) return false;
      memcpy(dst + pixel * 2, animationData + pos, bytes);
      pos += bytes;
    }
    pixel += count;
  }
  return pixel == 240 * 240;
}

void setup() {
  DEV_Module_Init();
  DEV_SET_Backlight(0);
  Serial.println("ConnectorDisplay: simulated voltage rise/drop, alternating success/failure");
  LCD_1IN28_Init(HORIZONTAL);
  if (!applyFrame(0, 0)) {
    Serial.println("ANIMATION_ERROR: invalid first frame");
    while (true) delay(1000);
  }
  LCD_1IN28_Display(frame);
  DEV_SET_Backlight(80);
  displayedFrames = 1;
  frameIndex = 1;
  nextFrameAt = millis() + kFrameMs;
  Serial.printf("DISPLAY_READY: 240x240 RGB565, 10 fps, %u animation bytes\n", sizeof(animationData));
  Serial.println("ANIMATION_STATE: GREEN_SUCCESS");
}

void loop() {
  if (static_cast<int32_t>(millis() - nextFrameAt) < 0) { delay(1); return; }
  const uint32_t started = millis();
  if (!applyFrame(state, frameIndex)) {
    Serial.printf("ANIMATION_ERROR: state=%u frame=%u\n", state, frameIndex);
    while (true) delay(1000);
  }
  LCD_1IN28_Display(frame);
  displayedFrames++;
  if (frameIndex == 0 || frameIndex == 5 || frameIndex == 16 || frameIndex == 34) {
    const uint16_t millivolts = frameIndex >= 34 || frameIndex <= 4 ? 0 : min(24000, (frameIndex - 4) * 2000);
    const char *stage = frameIndex == 34 ? "DROP" : frameIndex == 16 ? "HOLD" : frameIndex == 5 ? "RISING" : "IDLE";
    Serial.printf("SIMULATED_VOLTAGE state=%u millivolts=%u stage=%s\n", state, millivolts, stage);
  }
  if (frameIndex == 0) Serial.printf("ANIMATION_STATE: %s\n", state ? "RED_FAILURE" : "GREEN_SUCCESS");
  frameIndex++;
  if (frameIndex == kFramesPerState) { frameIndex = 0; state ^= 1; }
  nextFrameAt += kFrameMs;
  if (static_cast<int32_t>(millis() - nextFrameAt) >= 0) nextFrameAt = millis() + 1;
  if (millis() - lastReport >= 5000) {
    lastReport = millis();
    Serial.printf("DISPLAY_ALIVE frames=%lu render_ms=%lu free_heap=%u\n", displayedFrames, millis()-started, ESP.getFreeHeap());
  }
}
