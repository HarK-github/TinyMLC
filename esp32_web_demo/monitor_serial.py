#!/usr/bin/env python3
"""Interactive serial monitor for the ESP32."""

import sys
import time
import serial

PORT = "/dev/ttyUSB0"
BAUD = 115200

def main():
    try:
        # Open port with DTR and RTS explicitly set to False (Normal Run Mode)
        ser = serial.Serial(PORT, BAUD, timeout=0.1)
        ser.dtr = False
        ser.rts = False
    except Exception as e:
        print(f"Failed to open {PORT}: {e}", file=sys.stderr)
        sys.exit(1)

    print("==================================================", flush=True)
    print(f" Connected to {PORT} at {BAUD} baud", flush=True)
    print(" (If you want to see the bootup banner, tap the EN/RST button on your board)", flush=True)
    print(" Press Ctrl+C anytime to exit.", flush=True)
    print("==================================================\n", flush=True)

    try:
        while True:
            if ser.in_waiting:
                chunk = ser.read(ser.in_waiting).decode("utf-8", errors="replace")
                # Filter out raw ROM boot noise
                clean_chunk = "".join(ch for ch in chunk if ch in "\n\r\t" or ord(ch) >= 32)
                sys.stdout.write(clean_chunk)
                sys.stdout.flush()
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\n\n[Disconnected]")
    finally:
        ser.dtr = False
        ser.rts = False
        ser.close()

if __name__ == "__main__":
    main()
