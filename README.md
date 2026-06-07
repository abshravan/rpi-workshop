# Raspberry Pi Workshop — From Basics to AI & Home Servers

> **IEEE COMMSOC Workshop** · Speaker: A B Shravan Krishna  
> All programs from the live workshop in one cloneable repository.

---

## Quick Start

```bash
git clone https://github.com/abshravan/rpi-workshop.git
cd rpi-workshop
pip install -r requirements.txt
```

---

## Repository Structure

```
rpi-workshop/
├── 01_linux_basics/
│   ├── cheatsheet.sh          # 10 essential Linux commands
│   └── activity01.sh          # Activity 01 — your first folder on the Pi
│
├── 02_gpio_led/
│   └── blink.py               # "Hello World" — blink an LED on GPIO 17
│
├── 03_dht22_sensor/
│   └── dht22.py               # Read temperature & humidity from DHT22
│
├── 04_adxl345_accelerometer/
│   └── tilt.py                # Pitch & roll angles from ADXL345 over I²C
│
├── 05_camera/
│   ├── snap.py                # Capture a still photo
│   └── watch.py               # Motion detection from camera feed
│
├── 06_local_llm/
│   ├── setup_ollama.sh        # Install Ollama + pull TinyLlama
│   ├── chat.sh                # Start an interactive LLM chat
│   └── ollama_api_example.py  # Query Ollama's REST API from Python
│
├── wiring_diagrams/
│   └── README.md              # Text-based pin reference for all circuits
│
├── requirements.txt
└── README.md                  # This file
```

---

## What You Need

### Hardware

| Item | Notes |
|------|-------|
| Raspberry Pi (3B+ / 4 / 5) | Pi 4 / 5 recommended for the AI demos |
| microSD card ≥ 16 GB | Class 10 or better |
| USB-C / micro-USB power supply | 5 V 3 A for Pi 4/5 |
| LED + 330 Ω resistor | Any colour works |
| DHT22 sensor + 10 kΩ resistor | Temperature & humidity |
| ADXL345 breakout board | 3-axis accelerometer, I²C |
| Pi Camera Module (any version) | CSI ribbon cable |
| Jumper wires + breadboard | |

### Software

- **Raspberry Pi OS** (Bookworm, 64-bit recommended) — [rpi.imager](https://www.raspberrypi.com/software/)
- Python 3.9+ (pre-installed)
- `pip` packages — see `requirements.txt`

---

## Programs — Detailed Guide

### 01 · Linux Basics

#### `01_linux_basics/activity01.sh`

The very first hands-on activity. Opens a terminal on the Pi and practises navigation:

```bash
mkdir workshop         # create a folder
cd workshop            # enter it
nano notes.txt         # open text editor (save: Ctrl-O → Enter → Ctrl-X)
cat notes.txt          # print the file
```

#### `01_linux_basics/cheatsheet.sh`

Quick reference for the 10 commands covered in the workshop:

| Command | Purpose |
|---------|---------|
| `pwd` | Print current directory |
| `ls -la` | List files (long format + hidden) |
| `cd <dir>` | Change directory |
| `mkdir <dir>` | Create directory |
| `cp a b` | Copy file |
| `mv a b` | Move / rename file |
| `rm <file>` | Delete file |
| `cat <file>` | Print file |
| `nano <file>` | Edit file |
| `sudo apt update` | Refresh package list |

---

### 02 · GPIO LED — Hello Blinking World

#### `02_gpio_led/blink.py`

The GPIO equivalent of "Hello, World!" — blinks an LED on **GPIO 17** every second.

**Wiring:**
```
GPIO 17 (pin 11) → 330 Ω → LED (+) → LED (–) → GND (pin 6)
```

**Run:**
```bash
python3 02_gpio_led/blink.py
```

`gpiozero` is pre-installed on Raspberry Pi OS. If missing:
```bash
sudo apt install python3-gpiozero
```

> **Safety:** GPIO pins operate at **3.3 V**. Always use a current-limiting resistor (330 Ω) in series with an LED. Never connect GPIO directly to 5 V.

---

### 03 · DHT22 — Temperature & Humidity Sensor

#### `03_dht22_sensor/dht22.py`

Reads temperature (°C) and relative humidity (%) every 2 seconds. Handles occasional read errors gracefully.

**Wiring:**
```
3.3 V (pin 1)  → VCC
GPIO 4 (pin 7) → DATA  (+ 10 kΩ pull-up resistor to 3.3 V)
GND   (pin 6)  → GND
```

**Install:**
```bash
pip install adafruit-circuitpython-dht
sudo apt install libgpiod2
```

**Run:**
```bash
python3 03_dht22_sensor/dht22.py
```

**Sample output:**
```
  Temp (°C)  Humidity (%)
-------------------------
     24.5           58.0
     24.6           57.8
```

> **Note:** The DHT22 returns occasional `RuntimeError` read failures — this is normal sensor behaviour. The script catches and prints them, then retries.

---

### 04 · ADXL345 — Tilt & Motion Detection

#### `04_adxl345_accelerometer/tilt.py`

Reads raw X/Y/Z acceleration at 10 Hz over I²C and converts to **pitch** and **roll** angles.

**Enable I²C first:**
```bash
sudo raspi-config
# → Interface Options → I2C → Enable → Reboot
```

**Verify sensor is visible:**
```bash
i2cdetect -y 1
# Should show: 53  (the ADXL345's default I²C address)
```

**Wiring (I²C):**
```
3.3 V (pin 1)  → VCC
GND   (pin 6)  → GND
GPIO 2 (pin 3) → SDA
GPIO 3 (pin 5) → SCL
```

**Install:**
```bash
pip install adafruit-circuitpython-adxl34x
```

**Run:**
```bash
python3 04_adxl345_accelerometer/tilt.py
```

**Sample output:**
```
 Pitch (°)   Roll (°)
-----------------------
     +2.3       -45.1
     +2.2       -30.0
```

---

### 05 · Pi Camera

#### `05_camera/snap.py` — Still Photo

Captures a single image and saves it as `snap.jpg`.

**Enable camera:**
```bash
sudo raspi-config
# → Interface Options → Camera → Enable → Reboot
```

**Run:**
```bash
python3 05_camera/snap.py
ls -lh snap.jpg
```

`picamera2` is pre-installed on Raspberry Pi OS (Bookworm+).

---

#### `05_camera/watch.py` — Motion Detection

Continuously captures video frames, converts to grayscale, and flags frames where the mean absolute pixel difference between consecutive frames exceeds a threshold.

**Install:**
```bash
pip install opencv-python
```

**Run:**
```bash
python3 05_camera/watch.py
```

**Tune sensitivity** by editing the `THRESHOLD` constant (default `8`):
- Lower value → more sensitive (triggers on small movement)
- Higher value → less sensitive (only large movement triggers)

---

### 06 · Local LLM with Ollama

Run a large language model **fully offline** on the Raspberry Pi — no internet, no API key.

#### `06_local_llm/setup_ollama.sh` — Install & Pull Model

```bash
chmod +x 06_local_llm/setup_ollama.sh
./06_local_llm/setup_ollama.sh
```

This installs Ollama and pulls **TinyLlama (1.1 B)**, the fastest model that fits on a Pi.

#### `06_local_llm/chat.sh` — Interactive Chat

```bash
chmod +x 06_local_llm/chat.sh
./06_local_llm/chat.sh            # defaults to tinyllama
./06_local_llm/chat.sh phi3:mini  # use a smarter model
```

Type `/bye` or press `Ctrl-D` to exit.

#### `06_local_llm/ollama_api_example.py` — Python API

Query Ollama's REST API from a Python script (e.g., to embed it in another project):

```bash
ollama serve &                           # start the server
python3 06_local_llm/ollama_api_example.py
```

**Recommended models for Raspberry Pi:**

| Model | Params | Disk | Speed on Pi 4 | Notes |
|-------|--------|------|---------------|-------|
| `tinyllama` | 1.1 B | ~700 MB | ~10 tok/s | Fastest, good for demos |
| `phi3:mini` | 3.8 B | ~2.4 GB | ~3 tok/s | Much smarter |
| `gemma2:2b` | 2 B | ~1.6 GB | ~5 tok/s | Google's small model |

Pull additional models with:
```bash
ollama pull phi3:mini
ollama pull gemma2:2b
```

---

## Wiring Diagrams

See [`wiring_diagrams/README.md`](wiring_diagrams/README.md) for full text-based pin references and the 40-pin GPIO header map.

---

## Self-Hosted Apps (via CasaOS)

The workshop demo shows these apps running on a Pi — install CasaOS and deploy them from its app store:

| App | What it does |
|-----|-------------|
| **Jellyfin** | Home media server ("your own Netflix") |
| **Nextcloud** | File storage ("your own Google Drive") |
| **Pi-hole** | Network-wide ad blocker |
| **Immich** | Photo library ("your own Google Photos") |
| **Home Assistant** | Smart-home control centre |
| **Ollama + Open WebUI** | Local LLM with a ChatGPT-style interface |

Install CasaOS:
```bash
curl -fsSL get.casaos.io | sudo bash
```

---

## Project Ideas

### Beginner
- **Phone-controlled LED** — Flask web server with a button that toggles a GPIO pin
- **Room temperature logger** — DHT22 + CSV file or SQLite database
- **Motion-triggered alarm** — `watch.py` + buzzer or email notification

### Intermediate
- **Home-automation dashboard** — Home Assistant + DHT22 + relay modules
- **AI security camera** — `watch.py` + object detection with a MobileNet model
- **Voice-controlled assistant** — Whisper (speech-to-text) + Ollama + text-to-speech

### Advanced
- **Smart mirror** — Raspberry Pi + two-way mirror + Home Assistant widgets
- **Autonomous robot** — Pi + motor HAT + ultrasonic sensors + decision logic
- **Self-hosted AI home server** — Ollama + Open WebUI + Nextcloud on a single Pi

---

## 30-Day Challenge

| Week | Focus | Goal |
|------|-------|------|
| 1 | Linux & GPIO | Blink an LED from a web page |
| 2 | Sensors | Log temperature to a database and plot it |
| 3 | Camera + AI | Detect motion and save a snapshot |
| 4 | Home server | Deploy at least two self-hosted apps |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `gpiozero` not found | `sudo apt install python3-gpiozero` |
| `libgpiod2` missing (DHT error) | `sudo apt install libgpiod2` |
| ADXL345 not found by `i2cdetect` | Enable I²C in `raspi-config`; check wiring |
| Camera: "no cameras available" | Enable camera in `raspi-config`; reboot |
| Ollama install fails | Check internet connection; need ~1 GB free disk space |
| LED doesn't blink | Check resistor value, LED polarity, and GPIO pin number |

---

## License

MIT — free to use, modify, and share.

---

*Workshop slides: "Raspberry Pi — From Basics to AI & Home Servers" · IEEE COMMSOC 2026*
