# TMLC ESP32 / ESP32-S3 Live MNIST Digit Classifier Demo

An interactive, zero-cloud TinyML demonstration running a deep neural network compiled by **TMLC (TinyML Model-to-C Compiler)** directly on an **ESP32** microcontroller.

The ESP32 creates its own standalone Wi-Fi hotspot (`TMLC-ESP32-MNIST`) and hosts a responsive web application from its internal Flash memory. Anyone in the room can connect their smartphone, draw a handwritten digit with their finger, and watch the microcontroller classify it in **real time (~1–2 ms)**.

---

## 1. Key Metrics & Embedded Footprint

| Metric | Measurement / Specification | Engineering Significance |
|---|---|---|
| **Neural Network Architecture** | $784 \to 128 \to 64 \to 10$ (3 Dense Layers + ReLU + Softmax) | Real-world computer vision classification |
| **Quantization Scheme** | Symmetric per-tensor int8 weight quantization | Generated ahead-of-time by TMLC (`--quantize int8`) |
| **Flash Weight Storage** | **110,004 bytes (107.4 KB)** | **3.98&times; reduction** vs float32 (437.5 KB) |
| **Working SRAM Allocation** | **768 bytes** | Bipartite ping-pong static buffers (`buf_a` + `buf_b`) |
| **Dynamic Memory Allocation** | **0 bytes** | Zero `malloc()`, `calloc()`, `realloc()`, or `free()` |
| **Inference Latency** | **~1,100 to 1,500 &mu;s (1.1–1.5 ms)** | Measured on-chip using hardware timer `micros()` |
| **External Dependencies** | **None** | Pure C99 kernel + standard Arduino `<WiFi.h>` & `<WebServer.h>` |
| **Internet / Cloud Dependency** | **100% Offline** | Standalone SoftAP hotspot, runs anywhere without a router |

---

## 2. Project Directory Structure

```text
esp32_web_demo/
├── esp32_web_demo.ino   # Arduino C++ sketch (Wi-Fi AP, WebServer routes, inference handler)
├── index_html.h         # Responsive HTML5/CSS/JS drawing UI stored in Flash (PROGMEM)
├── model.h              # Auto-generated C99 public header from TMLC
├── model.c              # Auto-generated C99 implementation (int8 weights & MAC kernels)
├── platformio.ini       # PlatformIO project configuration for one-command build/flash
├── test_server.py       # Desktop simulator (test the web UI and C99 model on PC)
└── README.md            # Setup, flashing, and presentation instructions
```

---

## 3. How the System Works

```text
┌────────────────────────────────────────────────────────┐
│               Smartphone / Laptop Browser               │
│                                                        │
│  1. Connects to Wi-Fi AP: "TMLC-ESP32-MNIST"           │
│  2. Navigates to http://192.168.4.1                    │
│  3. User draws digit with finger on HTML5 <canvas>     │
│  4. Client-side JS centers & scales into 28x28 (784 B) │
│  5. Sends HTTP POST /predict (1,568 hex characters)    │
└───────────────────────────┬────────────────────────────┘
                            │ Wi-Fi HTTP POST
                            ▼
┌────────────────────────────────────────────────────────┐
│            ESP32 / ESP32-S3 Microcontroller            │
│                                                        │
│  6. Decodes hex payload into float input[784]          │
│  7. Measures start timestamp: t0 = micros()            │
│  8. Executes C99 model_predict(input, output)          │
│  9. Measures end timestamp:   t1 = micros()            │
│ 10. Computes argmax class & confidence percentage      │
│ 11. Returns JSON response:                             │
│     {"digit": 7, "confidence": 98.4, "latency_us": 1140}
└───────────────────────────┬────────────────────────────┘
                            │ HTTP JSON Response
                            ▼
┌────────────────────────────────────────────────────────┐
│               Smartphone / Laptop Browser               │
│                                                        │
│  12. UI displays predicted digit (e.g., "7")           │
│  13. Telemetry chips update with exact latency & RAM   │
│  14. 10-class horizontal probability bars animate live │
└────────────────────────────────────────────────────────┘
```

---

## 4. Hardware Requirements

- **Microcontroller**: Any standard **ESP32** or **ESP32-S3** development board (e.g., ESP32-WROOM-32, NodeMCU-32S, ESP32-S3-DevKitC-1).
- **Power**: Standard Micro-USB / USB-C cable connected to a laptop or portable 5V power bank.
- **Client Device**: Any smartphone (iPhone / Android) or laptop with a web browser.

---

## 5. Flashing to ESP32

You can flash using either **Arduino IDE** or **PlatformIO**.

### Method A: Arduino IDE (GUI)

1. **Install Arduino IDE** (v2.x recommended).
2. **Add ESP32 Board Support**:
   - Go to `File` &rarr; `Preferences`.
   - In *Additional Board Manager URLs*, add:
     ```text
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to `Tools` &rarr; `Board` &rarr; `Boards Manager`, search for `esp32`, and click **Install**.
3. **Open the Sketch**:
   - Open `esp32_web_demo/esp32_web_demo.ino` in Arduino IDE.
4. **Configure Board Settings**:
   - `Tools` &rarr; `Board` &rarr; select **ESP32 Dev Module** (or **ESP32S3 Dev Module**).
   - `Tools` &rarr; `Partition Scheme` &rarr; select **Huge APP (3MB No OTA/1MB SPIFFS)**.
     *(Required because the Wi-Fi stack + int8 model exceeds the default 1.2 MB app partition).*
   - `Tools` &rarr; `Port` &rarr; select your connected ESP32 COM / Serial port.
5. **Upload**:
   - Click the **Upload** button ($\rightarrow$).
   - Open the **Serial Monitor** at **115200 baud** to see initialization logs and IP address.

---

### Method B: PlatformIO (Command Line / VS Code)

If you use VS Code with PlatformIO or the PlatformIO CLI:

```bash
cd esp32_web_demo

# Build and flash for standard ESP32:
pio run -e esp32 -t upload

# Or build and flash for ESP32-S3:
pio run -e esp32s3 -t upload

# Open serial monitor:
pio device monitor -b 115200
```

---

## 6. How to Run the Live Demo (Step-by-Step Presentation Guide)

1. **Power On**: Plug the ESP32 into a USB port or portable power bank.
2. **Connect Phone to Wi-Fi**:
   - On your smartphone (or presentation laptop), open Wi-Fi settings.
   - Connect to the network: **`TMLC-ESP32-MNIST`**.
   - *(Note: It is an open hotspot; no password is required. It has no external internet connection, which is normal).*
3. **Open Browser**:
   - Open Chrome, Safari, or Firefox on your phone.
   - Navigate to:
     ```text
     http://192.168.4.1
     ```
4. **Draw and Classify**:
   - Draw any digit from `0` to `9` inside the box using your finger.
   - As soon as you lift your finger (with *Auto-classify* enabled), the phone sends the stroke data to the ESP32.
   - The ESP32 classifies the digit in **~1.1 ms** and animates the predicted digit and probability distribution.
5. **Benchmark Verification (Ground Truth)**:
   - Tap any of the preset buttons (**Test 0**, **Test 1**, **Test 3**, **Test 7**, **Test 8**).
   - These load verified sample images from the MNIST `t10k` test set directly into the drawing canvas and run inference, providing mathematical proof of classification accuracy.

---

## 7. Zero-Hardware Desktop Simulator (`test_server.py`)

If you want to test the exact web dashboard and compiled C99 kernel on your PC before flashing to hardware:

```bash
# From the project root:
python esp32_web_demo/test_server.py
```

1. It automatically compiles `model.c` into a shared library using GCC on your machine.
2. It starts a local web server at `http://localhost:8080`.
3. Open `http://localhost:8080` in your browser. You can draw digits with your mouse or test sample buttons; inference executes using the exact same C99 code generated by TMLC.

---

## 8. What to Highlight to Evaluators & Reviewers

1. **Flash Compression**: Highlight that uncompressed float32 weights require 437.5 KB, whereas TMLC's symmetric per-tensor int8 quantization compresses them to **110 KB (3.98&times; reduction)** with zero retraining.
2. **Extreme RAM Efficiency**: Point out the telemetry bar showing **768 Bytes of peak working SRAM**. While interpreters like TensorFlow Lite Micro allocate dynamic arena heaps, TMLC allocates exactly two static ping-pong buffers (`buf_a` and `buf_b`).
3. **Predictable Deterministic Execution**: Zero `malloc` calls mean no heap fragmentation, zero risk of out-of-memory crashes during the live demonstration, and deterministic sub-2 ms latency.
