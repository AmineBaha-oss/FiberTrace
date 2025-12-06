# FiberTrace - Cotton Bale Purity Scanner

A Raspberry Pi-based system that automatically classifies cotton bales as pure (good) or poly-blend (bad) using computer vision, then routes them to the appropriate bin using a servo-controlled gate.

## 🎯 What It Does

- **White paper** = GOOD (pure cotton bale) → Green LED + Gate to Good bin
- **Blue paper** = BAD (poly-blend bale) → Red LED + Gate to Bad bin

The system takes a photo, analyzes the color, and automatically routes items while tracking statistics in both a terminal dashboard and a web-based Flask dashboard.

## 📋 Hardware Requirements

- Raspberry Pi (any model with GPIO pins)
- Raspberry Pi Camera Module (or USB webcam)
- 2x LEDs (Green and Red)
- 2x 220Ω-330Ω resistors (for LEDs)
- 1x Micro servo motor (e.g., SG90)
- Breadboard and jumper wires
- Power supply for Raspberry Pi

## 🔌 Wiring Instructions

### GPIO Pin Mapping (BCM Mode)

| Component | GPIO (BCM) | Physical Pin | Notes |
|-----------|------------|--------------|-------|
| Green LED | GPIO 17 | Pin 11 | Good bale indicator |
| Red LED | GPIO 27 | Pin 13 | Bad bale indicator |
| Servo Signal | GPIO 18 | Pin 12 | PWM-capable pin |
| 5V Power | - | Pin 2 or 4 | For servo power |
| GND | - | Pin 6, 9, or 14 | Common ground |

### Detailed Wiring

#### Servo Motor (3 wires)
1. **Red wire** → Pi **5V** (Physical Pin 2 or 4)
2. **Brown/Black wire** → Pi **GND** (Physical Pin 6, 9, or 14)
3. **Orange/Yellow/White wire** → **GPIO 18** (Physical Pin 12)

#### Green LED (Good indicator)
1. **Long leg (anode)** → One side of **220Ω resistor**
2. **Other side of resistor** → **GPIO 17** (Physical Pin 11)
3. **Short leg (cathode)** → **GND** (same GND rail as servo)

#### Red LED (Bad indicator)
1. **Long leg (anode)** → One side of **220Ω resistor**
2. **Other side of resistor** → **GPIO 27** (Physical Pin 13)
3. **Short leg (cathode)** → **GND** (same GND rail)

#### Camera
- Connect Raspberry Pi Camera Module ribbon cable to the **CSI port** on the Pi
- Make sure camera is enabled in `raspi-config`:
  ```bash
  sudo raspi-config
  # Navigate to: Interface Options → Camera → Enable
  ```

### Visual Pin Reference

```
    3.3V  [1]  [2]  5V
   GPIO2  [3]  [4]  5V
   GPIO3  [5]  [6]  GND
   GPIO4  [7]  [8]  GPIO14
     GND  [9]  [10] GPIO15
  GPIO17  [11] [12] GPIO18  ← Servo Signal
  GPIO27  [13] [14] GND     ← Red LED
  GPIO22  [15] [16] GPIO23
    3.3V  [17] [18] GPIO24
  GPIO10  [19] [20] GND
   GPIO9  [21] [22] GPIO25
  GPIO11  [23] [24] GPIO8
     GND  [25] [26] GPIO7
```

**Key pins for this project:**
- Pin 11 (GPIO 17) → Green LED
- Pin 12 (GPIO 18) → Servo signal
- Pin 13 (GPIO 27) → Red LED
- Pin 2 or 4 → 5V (servo power)
- Pin 6, 9, or 14 → GND

## 🚀 Installation

### 1. Clone the Repository

On your Raspberry Pi:

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/FiberTrace.git
cd FiberTrace
```

### 2. Install Dependencies

```bash
sudo apt update
sudo apt install -y python3-opencv python3-rpi.gpio python3-pip
pip3 install -r requirements.txt
```

### 3. Enable Camera (if using Pi Camera Module)

```bash
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable
# Reboot after enabling
sudo reboot
```

## 💻 Usage

### Running the Demo Script

The main demo script scans items when you press Enter:

```bash
python3 fibertrace_demo.py
```

**Instructions:**
1. Place white or blue paper under the camera
2. Press ENTER in the terminal to scan
3. Watch LEDs light up, servo move, and dashboard update

### Running the Flask Dashboard

In a separate terminal (or run in background):

```bash
python3 app.py
```

Then open a web browser and navigate to:
- **Local:** http://localhost:5000
- **From another device:** http://<raspberry-pi-ip>:5000

The dashboard updates automatically every 2 seconds with real-time statistics.

### Running Both Together

You can run both simultaneously:

```bash
# Terminal 1: Demo script
python3 fibertrace_demo.py

# Terminal 2: Flask dashboard
python3 app.py
```

## 📊 Features

- **Automatic Classification:** Uses OpenCV to analyze color and classify bales
- **Visual Feedback:** Green/Red LEDs indicate classification result
- **Servo Gate Control:** Automatically routes items to correct bin
- **Terminal Dashboard:** Real-time statistics in the console
- **Web Dashboard:** Beautiful Flask-based web interface
- **Data Persistence:** Statistics saved to JSON file

## 🔧 Configuration

You can adjust these values in `fibertrace_demo.py`:

```python
GOOD_ANGLE = 40    # Servo angle for Good bin
BAD_ANGLE  = 140   # Servo angle for Bad bin
CENTER_ANGLE = 90  # Neutral position
```

Adjust these angles based on your physical setup.

## 🐛 Troubleshooting

### Camera not working
- Check camera connection and enable in `raspi-config`
- Try different camera index: `cv2.VideoCapture(1)` instead of `0`
- For libcamera: `cv2.VideoCapture(0, cv2.CAP_V4L2)`

### Servo not moving
- Check wiring (signal to GPIO 18, power to 5V, ground to GND)
- If Pi reboots when servo moves, use external 5V power supply
- Verify servo is getting power (red wire to 5V)

### LEDs not lighting
- Check resistor is connected (220Ω-330Ω)
- Verify GPIO pins (17 for green, 27 for red)
- Test with multimeter if needed

### Flask dashboard not accessible
- Make sure firewall allows port 5000: `sudo ufw allow 5000`
- Check Pi's IP address: `hostname -I`
- Ensure `fibertrace_demo.py` has run at least once to create data file

## 📁 Project Structure

```
FiberTrace/
├── fibertrace_demo.py    # Main demo script
├── app.py                 # Flask dashboard server
├── templates/
│   └── dashboard.html     # Web dashboard UI
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── fibertrace_data.json  # Statistics data (created at runtime)
```

## 🔮 Future Enhancements

- Button trigger instead of Enter key
- Automatic conveyor belt detection
- Machine learning model for better classification
- Database storage for historical data
- Email/SMS alerts for low purity
- Modular refactoring (like YVLSWITCH project)

## 📝 License

This project is open source and available for educational purposes.

## 👥 Credits

Built for automated cotton bale quality control using Raspberry Pi and computer vision.

