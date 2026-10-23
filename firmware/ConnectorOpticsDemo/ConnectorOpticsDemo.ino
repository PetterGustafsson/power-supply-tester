// Exact 240x240 RGB565 connector art, played from the FFat flash partition.
// This is an explicitly SIMULATED display demo; no pin or voltage is sampled.
#include <Arduino.h>
#include <strings.h>
#include <esp_partition.h>
#include <miniz.h>
#include <esp_heap_caps.h>
#include "DEV_Config.h"
#include "LCD_1in28.h"

// The display loop does not inflate; a second-core worker owns the decoder.
SET_LOOP_TASK_STACK_SIZE(8192);

// Required by the Waveshare driver (also used by its Clear helper).
UWORD frame[240 * 240];
UWORD *BlackImage = frame;

namespace {
constexpr uint32_t kWidth = 240;
constexpr uint32_t kPixels = kWidth * kWidth;
constexpr uint32_t kFrameBytes = kPixels * 2;
constexpr uint32_t kFramePeriodUs = 20000;
constexpr uint32_t kMainFrames = 500;
constexpr uint32_t kStormFrames = 100;
constexpr uint32_t kMaxCompressedBytes = 50000;

struct __attribute__((packed)) AssetHeader {
  char magic[8];
  uint32_t version, width, fps, mainFrames, stormFrames;
  uint32_t payloadOffset, payloadBytes, payloadCrc;
};
struct __attribute__((packed)) FrameMeta {
  uint32_t offset, length;
  uint8_t x0, y0, x1, y1, flags;
};
static_assert(sizeof(AssetHeader) == 40, "Bad asset header layout");
static_assert(sizeof(FrameMeta) == 13, "Bad frame metadata layout");

enum Mode : uint8_t { FULL, IDLE, HELIX, STORM };
const char *modeName(Mode mode) {
  switch (mode) {
    case FULL: return "FULL";
    case IDLE: return "IDLE";
    case HELIX: return "HELIX";
    case STORM: return "STORM";
  }
  return "UNKNOWN";
}
uint16_t rangeStart(Mode mode) { return mode == HELIX ? 250 : mode == STORM ? 500 : 0; }
uint16_t rangeEnd(Mode mode) { return mode == IDLE ? 140 : mode == HELIX ? 300 : mode == STORM ? 600 : 500; }

const esp_partition_t *assetPartition = nullptr;
AssetHeader assetHeader;
uint8_t *compressed = nullptr;
uint8_t *delta = nullptr;
// The LCD driver sends the framebuffer byte for byte; bytes are RGB565 big-endian.
Mode mode = FULL;
uint16_t frameIndex = 0;
uint32_t nextFrameUs = 0;
uint32_t reportAtMs = 0;
uint32_t rendered = 0, reportRendered = 0;
uint64_t decodeUs = 0, transferUs = 0;
char command[24];
uint8_t commandLength = 0;
struct DecodeRequest { uint16_t index; };
struct DecodeResult {
  FrameMeta meta;
  uint16_t index;
  uint8_t error;
  uint32_t elapsedUs;
};
QueueHandle_t decodeRequests = nullptr;
QueueHandle_t decodeResults = nullptr;

[[noreturn]] void stopWithError(const char *reason) {
  Serial.printf("DISPLAY_ERROR: %s\n", reason);
  for (;;) delay(1000);
}

bool readAsset(uint32_t offset, void *destination, size_t length) {
  if (offset > assetPartition->size || length > assetPartition->size - offset) return false;
  return esp_partition_read(assetPartition, offset, destination, length) == ESP_OK;
}

void decodeWorker(void *) {
  DecodeRequest request;
  for (;;) {
    xQueueReceive(decodeRequests, &request, portMAX_DELAY);
    DecodeResult result{};
    result.index = request.index;
    FrameMeta &meta = result.meta;
    if (!readAsset(sizeof(AssetHeader) + request.index * sizeof(FrameMeta), &meta, sizeof(meta)))
      result.error = 1;
    else if (!meta.length || meta.length > kMaxCompressedBytes ||
        meta.offset > assetHeader.payloadBytes ||
        meta.length > assetHeader.payloadBytes - meta.offset ||
        meta.x0 > meta.x1 || meta.x1 > kWidth ||
        meta.y0 > meta.y1 || meta.y1 > kWidth)
      result.error = 2;
    else {
      const uint32_t began = micros();
      if (!readAsset(assetHeader.payloadOffset + meta.offset, compressed, meta.length))
        result.error = 3;
      else if (tinfl_decompress_mem_to_mem(delta, kFrameBytes, compressed,
          meta.length, TINFL_FLAG_PARSE_ZLIB_HEADER) != kFrameBytes)
        result.error = 4;
      result.elapsedUs = micros() - began;
    }
    xQueueSend(decodeResults, &result, portMAX_DELAY);
  }
}

void queueFrame(uint16_t index) {
  DecodeRequest request { index };
  if (xQueueSend(decodeRequests, &request, 0) != pdTRUE) stopWithError("decode queue full");
}

DecodeResult takeFrame() {
  DecodeResult result;
  if (xQueueReceive(decodeResults, &result, pdMS_TO_TICKS(1000)) != pdTRUE)
    stopWithError("decode timeout");
  if (result.error) {
    Serial.printf("DISPLAY_ERROR: decode code=%u frame=%u\n", result.error, result.index);
    stopWithError("decode failed");
  }
  return result;
}

void applyFrame(const DecodeResult &ready) {
  uint8_t *pixels = reinterpret_cast<uint8_t *>(frame);
  if (ready.meta.flags & 1) memcpy(pixels, delta, kFrameBytes);
  else for (uint32_t byte = 0; byte < kFrameBytes; ++byte) pixels[byte] ^= delta[byte];
  decodeUs += ready.elapsedUs;
}

void transferFrame(const DecodeResult &ready) {
  const uint32_t transferStart = micros();
  const FrameMeta &meta = ready.meta;
  if (meta.flags & 1) LCD_1IN28_Display(frame);
  else if (meta.x1 > meta.x0 && meta.y1 > meta.y0)
    LCD_1IN28_DisplayWindows(meta.x0, meta.y0, meta.x1, meta.y1, frame);
  transferUs += micros() - transferStart;
  ++rendered;
}

uint16_t followingFrame(uint16_t index) {
  ++index;
  return index == rangeEnd(mode) ? rangeStart(mode) : index;
}

void selectMode(Mode selected) {
  takeFrame();  // Finish and discard the old mode's already queued decode.
  mode = selected;
  frameIndex = rangeStart(mode);
  queueFrame(frameIndex);
  const DecodeResult first = takeFrame();
  applyFrame(first);
  frameIndex = followingFrame(frameIndex);
  queueFrame(frameIndex);
  const uint32_t frameStart = micros();
  transferFrame(first);
  nextFrameUs = frameStart + kFramePeriodUs;
  Serial.printf("DISPLAY_MODE: %s SIMULATED\n", modeName(mode));
}

void processSerial() {
  while (Serial.available()) {
    char c = static_cast<char>(Serial.read());
    if (c == '\r' || c == '\n') {
      if (!commandLength) continue;
      command[commandLength] = '\0';
      if (!strcasecmp(command, "full")) selectMode(FULL);
      else if (!strcasecmp(command, "idle")) selectMode(IDLE);
      else if (!strcasecmp(command, "helix")) selectMode(HELIX);
      else if (!strcasecmp(command, "storm")) selectMode(STORM);
      else Serial.println("DISPLAY_COMMANDS: full idle helix storm");
      commandLength = 0;
    } else if (commandLength < sizeof(command) - 1) {
      command[commandLength++] = c;
    } else commandLength = 0;
  }
}

}  // namespace

void setup() {
  Serial.begin(115200);
  DEV_Module_Init();
  Serial.printf("DISPLAY_BOOT: OPTICS50 SIMULATED internal_heap=%u max_block=%u\n",
      ESP.getFreeHeap(), heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL));
  DEV_SET_Backlight(0);
  LCD_1IN28_Init(HORIZONTAL);
  assetPartition = esp_partition_find_first(ESP_PARTITION_TYPE_DATA,
      ESP_PARTITION_SUBTYPE_DATA_FAT, "ffat");
  if (!assetPartition) stopWithError("FFat partition missing");
  if (!readAsset(0, &assetHeader, sizeof(assetHeader))) stopWithError("asset header read");
  if (memcmp(assetHeader.magic, "OPTICS50", 8) || assetHeader.version != 1 ||
      assetHeader.width != kWidth || assetHeader.fps != 50 ||
      assetHeader.mainFrames != kMainFrames || assetHeader.stormFrames != kStormFrames ||
      assetHeader.payloadOffset != 8192 ||
      assetHeader.payloadOffset > assetPartition->size ||
      assetHeader.payloadBytes > assetPartition->size - assetHeader.payloadOffset)
    stopWithError("OPTICS50 asset missing or incompatible");
  compressed = static_cast<uint8_t *>(heap_caps_malloc(kMaxCompressedBytes, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
  delta = static_cast<uint8_t *>(heap_caps_malloc(kFrameBytes, MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT));
  const bool internalDelta = delta != nullptr;
  if (!delta) delta = static_cast<uint8_t *>(heap_caps_malloc(kFrameBytes, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
  if (!compressed || !delta) stopWithError("decode buffer allocation");
  Serial.printf("DISPLAY_MEMORY: delta_internal=%u free_heap=%u free_psram=%u\n",
      internalDelta ? 1 : 0, ESP.getFreeHeap(), ESP.getFreePsram());
  if (!internalDelta) stopWithError("internal decode buffer unavailable");
  memset(frame, 0, sizeof(frame));
  decodeRequests = xQueueCreate(1, sizeof(DecodeRequest));
  decodeResults = xQueueCreate(1, sizeof(DecodeResult));
  if (!decodeRequests || !decodeResults ||
      xTaskCreatePinnedToCore(decodeWorker, "opticsDecode", 24576, nullptr, 1, nullptr, 0) != pdPASS)
    stopWithError("decoder task allocation");
  queueFrame(0);
  const DecodeResult first = takeFrame();
  applyFrame(first);
  frameIndex = 1;
  queueFrame(frameIndex);
  const uint32_t firstAt = micros();
  transferFrame(first);
  DEV_SET_Backlight(80);
  reportAtMs = millis();
  nextFrameUs = firstAt + kFramePeriodUs;
  Serial.printf("DISPLAY_READY: OPTICS50 SIMULATED 240x240 RGB565 50 source fps, %lu asset bytes\n",
      static_cast<unsigned long>(assetHeader.payloadOffset + assetHeader.payloadBytes));
  Serial.println("DISPLAY_COMMANDS: full idle helix storm");
  Serial.println("DISPLAY_MODE: FULL SIMULATED");
}

void loop() {
  processSerial();
  const uint32_t now = micros();
  if (static_cast<int32_t>(now - nextFrameUs) >= 0) {
    const DecodeResult ready = takeFrame();
    if (ready.index != frameIndex) stopWithError("out-of-order frame");
    applyFrame(ready);
    frameIndex = followingFrame(frameIndex);
    queueFrame(frameIndex);  // Decode one frame ahead while the LCD transfers.
    transferFrame(ready);
    nextFrameUs += kFramePeriodUs;
    // Avoid an unbounded backlog if a frame takes longer than the target slot.
    if (static_cast<int32_t>(micros() - nextFrameUs) > static_cast<int32_t>(kFramePeriodUs))
      nextFrameUs = micros();
  } else delay(1);
  const uint32_t nowMs = millis();
  if (nowMs - reportAtMs >= 5000) {
    const uint32_t elapsed = nowMs - reportAtMs;
    const uint32_t count = rendered - reportRendered;
    Serial.printf("DISPLAY_ALIVE mode=%s frames=%lu fps_x10=%lu decode_us=%lu transfer_us=%lu free_heap=%u free_psram=%u\n",
        modeName(mode), static_cast<unsigned long>(rendered),
        static_cast<unsigned long>((count * 10000UL) / elapsed),
        static_cast<unsigned long>(count ? decodeUs / count : 0),
        static_cast<unsigned long>(count ? transferUs / count : 0),
        ESP.getFreeHeap(), ESP.getFreePsram());
    reportAtMs = nowMs;
    reportRendered = rendered;
    decodeUs = transferUs = 0;
  }
}
