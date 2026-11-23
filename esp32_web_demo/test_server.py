#!/usr/bin/env python3
"""Desktop simulator server for the TMLC ESP32 MNIST Web Demo.

Allows testing the exact web drawing interface and compiled C99 model on a PC
before deploying to physical ESP32 hardware.
"""

from __future__ import annotations

import ctypes
import http.server
import json
import os
import pathlib
import re
import socketserver
import subprocess
import sys
import time

PORT = 8080
DEMO_DIR = pathlib.Path(__file__).resolve().parent
MODEL_C = DEMO_DIR / "model.c"
MODEL_H = DEMO_DIR / "model.h"
INDEX_H = DEMO_DIR / "index_html.h"
LIB_SO = DEMO_DIR / ("model.dll" if sys.platform == "win32" else "libmodel.so")


def compile_shared_library() -> ctypes.CDLL:
    """Compile model.c into a shared library using host C compiler."""
    if not LIB_SO.is_file() or LIB_SO.stat().st_mtime < MODEL_C.stat().st_mtime:
        print(f"[Build] Compiling {MODEL_C.name} into shared library {LIB_SO.name}...")
        cmd = [
            "gcc",
            "-std=c99",
            "-O2",
            "-shared",
            "-fPIC",
            str(MODEL_C),
            "-o",
            str(LIB_SO),
            "-lm",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"GCC Compilation Error:\n{res.stderr}", file=sys.stderr)
            sys.exit(1)
        print("[Build] Shared library compiled successfully.")

    # Load shared library
    dll = ctypes.CDLL(str(LIB_SO))
    # void model_predict(const float input[784], float output[10]);
    dll.model_predict.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
    ]
    dll.model_predict.restype = None
    return dll


def extract_html() -> str:
    """Extract embedded raw HTML from index_html.h."""
    content = INDEX_H.read_text(encoding="utf-8")
    match = re.search(r'R"rawliteral\((.*?)\)rawliteral";', content, re.DOTALL)
    if not match:
        raise ValueError("Could not extract raw HTML from index_html.h")
    return match.group(1).strip()


class DemoHTTPHandler(http.server.BaseHTTPRequestHandler):
    model_dll: ctypes.CDLL | None = None
    html_content: str = ""

    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/?"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(self.html_content.encode("utf-8"))
        elif self.path == "/info":
            info = {
                "status": "online (PC Simulator)",
                "model": "MNIST",
                "architecture": "784 -> 128 -> 64 -> 10",
                "quantization": "int8 symmetric per-tensor",
                "flash_weight_bytes": 110004,
                "ram_peak_bytes": 768,
                "chip_model": "Host PC (Simulated ESP32)",
                "cpu_freq_mhz": 240,
                "free_heap_bytes": 298416,
            }
            payload = json.dumps(info).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self) -> None:
        if self.path == "/predict":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8").strip()

            in_arr = (ctypes.c_float * 784)()
            parsed = False

            # Case 1: Hex string
            if len(body) >= 1568:
                try:
                    raw_bytes = bytes.fromhex(body[:1568])
                    for i in range(784):
                        in_arr[i] = raw_bytes[i] / 255.0
                    parsed = True
                except ValueError:
                    parsed = False

            # Case 2: Comma-separated values
            if not parsed:
                try:
                    tokens = [float(x.strip()) for x in body.split(",") if x.strip()]
                    if len(tokens) == 784:
                        for i in range(784):
                            val = tokens[i]
                            if val > 1.0:
                                val /= 255.0
                            in_arr[i] = val
                        parsed = True
                except ValueError:
                    parsed = False

            if not parsed:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error":"Invalid 784-input payload"}')
                return

            out_arr = (ctypes.c_float * 10)()

            # Run inference and measure time
            t0 = time.perf_counter_ns()
            self.model_dll.model_predict(in_arr, out_arr)
            t1 = time.perf_counter_ns()
            latency_us = max(1, int((t1 - t0) / 1000))

            probs = [round(float(out_arr[i]) * 100.0, 2) for i in range(10)]
            pred_digit = int(max(range(10), key=lambda i: probs[i]))
            conf = probs[pred_digit]

            resp = {
                "status": "ok",
                "digit": pred_digit,
                "confidence": conf,
                "latency_us": latency_us,
                "probabilities": probs,
            }
            payload = json.dumps(resp).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args) -> None:
        # Clean logging
        sys.stdout.write(f"[Server] {args[0]} -> {args[1]}\n")


def main() -> None:
    dll = compile_shared_library()
    html = extract_html()

    DemoHTTPHandler.model_dll = dll
    DemoHTTPHandler.html_content = html

    # Allow fast address reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), DemoHTTPHandler) as httpd:
        print("==================================================")
        print("  TMLC Live MNIST Web Demo Desktop Simulator     ")
        print("==================================================")
        print(f"Server Running  : http://localhost:{PORT}")
        print("Press Ctrl+C to stop the simulator.")
        print("==================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")


if __name__ == "__main__":
    main()
