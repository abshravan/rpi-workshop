# Wiring Diagrams

Text-based pin reference for each circuit in this workshop.
Always work with the Pi **powered off** when connecting hardware.
GPIO logic level is **3.3 V** — never connect GPIO directly to a 5 V signal.

---

## LED (blink.py)

```
3.3 V / 5 V supply (pin 2) ─────────────────────────────── NOT used for LED
GPIO 17          (pin 11) ──── 330 Ω resistor ──── LED (+) ──── LED (–) ──── GND (pin 6)
```

| Pi Pin | Label    | → Component        |
|--------|----------|--------------------|
| 11     | GPIO 17  | 330 Ω → LED anode  |
| 6      | GND      | LED cathode        |

---

## DHT22 Temperature & Humidity (dht22.py)

```
3.3 V (pin 1)  ──────────── VCC  ──────── 10 kΩ pull-up ────┐
                                                              │
GPIO 4 (pin 7) ──────────── DATA ─────────────────────────── ┘
GND   (pin 6)  ──────────── GND
```

| Pi Pin | Label   | DHT22 Pin |
|--------|---------|-----------|
| 1      | 3.3 V   | VCC       |
| 7      | GPIO 4  | DATA (+ 10 kΩ pull-up to 3.3 V) |
| 6      | GND     | GND       |

---

## ADXL345 Accelerometer (tilt.py) — I²C

| Pi Pin | Label        | ADXL345 Pin |
|--------|--------------|-------------|
| 1      | 3.3 V        | VCC         |
| 6      | GND          | GND         |
| 3      | GPIO 2 (SDA) | SDA         |
| 5      | GPIO 3 (SCL) | SCL         |

Default I²C address: **0x53**
Verify with: `i2cdetect -y 1`

---

## Pi Camera Module

Connect the ribbon cable to the **CSI port** (between HDMI and audio jack).
The **blue side** of the ribbon faces the Ethernet/USB ports.

Enable via: `sudo raspi-config → Interface Options → Camera`

---

## GPIO 40-Pin Header Quick Reference

```
       3V3  (1) (2)  5V
     GPIO2  (3) (4)  5V
     GPIO3  (5) (6)  GND
     GPIO4  (7) (8)  GPIO14
       GND  (9) (10) GPIO15
    GPIO17 (11) (12) GPIO18
    GPIO27 (13) (14) GND
    GPIO22 (15) (16) GPIO23
       3V3 (17) (18) GPIO24
    GPIO10 (19) (20) GND
     GPIO9 (21) (22) GPIO25
    GPIO11 (23) (24) GPIO8
       GND (25) (26) GPIO7
     GPIO0 (27) (28) GPIO1
     GPIO5 (29) (30) GND
     GPIO6 (31) (32) GPIO12
    GPIO13 (33) (34) GND
    GPIO19 (35) (36) GPIO16
    GPIO26 (37) (38) GPIO20
       GND (39) (40) GPIO21
```
