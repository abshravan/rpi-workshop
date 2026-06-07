#!/usr/bin/env python3
"""
dht22.py — Temperature & Humidity logger
Reads from a DHT22 sensor every 2 seconds and prints the values.

Hardware wiring:
  DHT22 VCC   →  3.3 V (pin 1)
  DHT22 DATA  →  GPIO 4 (pin 7)  +  10 kΩ pull-up resistor to 3.3 V
  DHT22 GND   →  GND  (pin 6)

Install dependency:
  pip install adafruit-circuitpython-dht
  sudo apt install libgpiod2
"""

import time
import board
import adafruit_dht

dht = adafruit_dht.DHT22(board.D4)

print("Reading DHT22 on GPIO 4 — Ctrl-C to stop")
print(f"{'Temp (°C)':>10}  {'Humidity (%)':>12}")
print("-" * 25)

while True:
    try:
        temp = dht.temperature   # degrees Celsius
        rh   = dht.humidity      # relative humidity %
        print(f"{temp:>10.1f}  {rh:>12.1f}")
    except RuntimeError as e:
        # DHT22 occasionally produces read errors; this is normal
        print(f"  read error: {e}")
    time.sleep(2)
