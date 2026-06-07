#!/usr/bin/env python3
"""
blink.py — "Hello World" for GPIO
Blinks an LED connected to GPIO 17 (BCM) once per second.

Hardware:
  GPIO 17 (pin 11)  →  330 Ω resistor  →  LED anode (+)
  LED cathode (-)   →  GND (pin 6 or 9)

Install dependency:
  sudo apt install python3-gpiozero   # usually pre-installed on Pi OS
"""

from gpiozero import LED
from time import sleep

led = LED(17)

print("Blinking LED on GPIO 17 — Ctrl-C to stop")

while True:
    led.on()
    sleep(1)
    led.off()
    sleep(1)
