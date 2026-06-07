#!/usr/bin/env python3
"""
tilt.py — Tilt & motion detection with ADXL345
Reads X/Y/Z acceleration at 10 Hz and computes pitch & roll angles.

Hardware wiring (I²C):
  ADXL345 VCC  →  3.3 V (pin 1)
  ADXL345 GND  →  GND  (pin 6)
  ADXL345 SDA  →  GPIO 2 / SDA (pin 3)
  ADXL345 SCL  →  GPIO 3 / SCL (pin 5)

Enable I²C first:
  sudo raspi-config  →  Interface Options  →  I2C  →  Enable
  Verify:  i2cdetect -y 1   (should show address 0x53)

Install dependency:
  pip install adafruit-circuitpython-adxl34x
"""

import time
import math
import board
import busio
import adafruit_adxl34x

i2c   = busio.I2C(board.SCL, board.SDA)
accel = adafruit_adxl34x.ADXL345(i2c)
accel.range = adafruit_adxl34x.Range.RANGE_4_G

print("Reading ADXL345 — Ctrl-C to stop")
print(f"{'Pitch (°)':>10}  {'Roll (°)':>10}")
print("-" * 23)

while True:
    x, y, z = accel.acceleration          # m/s²
    pitch = math.degrees(math.atan2(y, z))
    roll  = math.degrees(math.atan2(x, z))
    print(f"{pitch:>+10.1f}  {roll:>+10.1f}")
    time.sleep(0.1)
