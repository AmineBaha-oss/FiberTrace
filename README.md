# FiberTrace - IoT Textile Sorting System

A Raspberry Pi-based IoT device that automatically classifies textile materials as pure cotton (good) or poly-blend (bad) using computer vision, then routes them to the appropriate bin using a servo-controlled gate. Features a professional industrial web dashboard for real-time monitoring and control.

##  What It Does

- **White/Light materials** = GOOD (pure cotton) → Green LED + Gate to Good bin
- **Blue/Dark materials** = BAD (poly-blend) → Red LED + Gate to Bad bin

The system:
- Captures images using a Raspberry Pi camera
- Analyzes color composition (RGB values) to calculate purity percentage
- Classifies each item with per-item purity (e.g., "95% Cotton, 5% Poly Blend")
- Controls hardware (LEDs, servo gate) automatically
- Tracks statistics in real-time
- Provides a professional web dashboard for monitoring and control

##  Hardware Requirements

- Raspberry Pi (any model with GPIO pins)
- Raspberry Pi Camera Module (or USB webcam)
- 2x LEDs (Green and Red)
- 2x 220Ω-330Ω resistors (for LEDs)
- 1x Micro servo motor (e.g., SG90)
- Breadboard and jumper wires
- Power supply for Raspberry Pi

##  Wiring Instructions

### GPIO Pin Mapping (BCM Mode)

| Component    | GPIO (BCM) | Physical Pin    | Notes               |
| ------------ | ---------- | --------------- | ------------------- |
| Green LED    | GPIO 17    | Pin 11          | Good bale indicator |
| Red LED      | GPIO 27    | Pin 13          | Bad bale indicator  |
| Servo Signal | GPIO 18    | Pin 12          | PWM-capable pin     |
| 5V Power     | -          | Pin 2 or 4      | For servo power     |
| GND          | -          | Pin 6, 9, or 14 | Common ground       |

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

##  Installation

### 1. Clone the Repository

On your Raspberry Pi:

```bash
cd ~
git clone https://github.com/AmineBaha-oss/FiberTrace.git
cd FiberTrace
```

### 2. Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3-opencv python3-rpi.gpio python3-pip python3-libcamera python3-picamera2 rpicam-apps
```

**Important:** `python3-libcamera` and `python3-picamera2` are system packages required for the Raspberry Pi camera. These work best when running without a virtual environment.

### 3. Install Python Dependencies (System-wide)

Since the camera requires system packages, we install Python dependencies system-wide:

```bash
pip3 install --break-system-packages Flask
```

**Note:** OpenCV (`python3-opencv`) and RPi.GPIO (`python3-rpi.gpio`) are already installed via apt.

### 4. Enable Camera

```bash
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable
# Reboot after enabling
sudo reboot
```

After reboot, verify camera works:

```bash
libcamera-hello -t 0
```

##  Usage

### Step 1: Test Hardware

Before running the main demo, test all hardware components:

```bash
cd ~/FiberTrace
python3 test_hardware.py
```

This will test:
- **Camera** - Takes a test photo and saves it
- **Green LED** - Blinks and asks for confirmation
- **Red LED** - Blinks and asks for confirmation
- **Servo motor** - Sweeps through angles (center → good → bad → center)

Fix any issues before proceeding.

### Step 2: Run the Flask Dashboard

The Flask dashboard provides a professional web interface with camera preview and scan control:

```bash
cd ~/FiberTrace
python3 app.py
```

The dashboard will start and show:
```
Starting FiberTrace Dashboard...
Access at: http://localhost:5000
Or from another device: http://<raspberry-pi-ip>:5000
```

**Access the dashboard:**
- **From Pi:** http://localhost:5000
- **From other devices:** http://192.168.0.114:5000 (use your Pi's IP)

### Step 3: Use the Dashboard

The web dashboard provides:

1. **Real-time Statistics:**
   - Total items processed
   - Bale purity percentage
   - Pure cotton count
   - Blend detections count

2. **Live Camera Preview:**
   - Shows last scanned image
   - Updates when you click "Scan Item"

3. **Scan Control:**
   - Click "Scan Item" button to trigger a scan
   - See result immediately (GOOD/BAD with purity %)
   - View composition breakdown (e.g., "95% Cotton, 5% Poly Blend")

4. **Purity Gauge:**
   - Visual circular gauge showing overall bale purity
   - Color-coded status (Green = Certified 98%+, Yellow = Good 90%+, Red = Needs Improvement)

5. **Production Statistics Table:**
   - Detailed metrics with timestamps
   - Last item purity and composition
   - Status indicators

### Alternative: Terminal Demo Script

You can also run the terminal-based demo:

```bash
cd ~/FiberTrace
python3 fibertrace_demo.py
```

**Instructions:**
1. Place white or blue paper under the camera
2. Press ENTER in the terminal to scan
3. Watch LEDs light up, servo move, and terminal dashboard update

**Note:** The Flask dashboard and terminal script share the same data file, so you can run both simultaneously if desired.

##  Features

### Core Functionality

- **Automatic Classification:** Uses OpenCV to analyze RGB color values and classify materials
- **Per-Item Purity Calculation:** Each scan calculates purity percentage (0-100%)
- **Composition Breakdown:** Shows exact blend ratio (e.g., "88% Cotton, 12% Poly Blend")
- **Visual Feedback:** Green/Red LEDs indicate classification result
- **Servo Gate Control:** Automatically routes items to correct bin
- **Real-time Statistics:** Tracks total scanned, good/bad counts, and overall purity

### Web Dashboard Features

- **Professional Industrial UI:** Dark theme with glassmorphism effects
- **Live Camera Preview:** Shows last scanned image
- **Scan Control:** Trigger scans directly from web interface
- **Animated Updates:** Smooth number animations and visual feedback
- **Scanning Animation:** Visual scanning line effect during scans
- **Real-time Updates:** Auto-refreshes every 2 seconds
- **Responsive Design:** Works on desktop, tablet, and mobile

### Technical Features

- **Camera Support:** Works with picamera2 (libcamera) and OpenCV fallback
- **Data Persistence:** Statistics saved to JSON file
- **Hardware Control:** Direct GPIO control for LEDs and servo
- **Error Handling:** Graceful fallbacks for camera issues

## 🔬 How It Works: Sensor Technology

### Light Detection Process

1. **Image Capture:** Camera sensor captures RGB image (640x480 pixels)
2. **Color Analysis:** Algorithm analyzes Red, Green, Blue channel values
3. **Purity Calculation:** 
   - White/light materials → High RGB values → High cotton purity
   - Blue materials → High blue, low red/green → Poly-blend detected
4. **Classification:** Threshold-based decision (blue dominant = blend)
5. **Hardware Response:** LEDs and servo gate respond instantly

### Detection Algorithm

- **Region of Interest:** Focuses on center 25% of image (most reliable)
- **Color Ratios:** Calculates percentage of each color channel
- **Purity Formula:** `cotton_purity = (red_ratio + green_ratio) * 100`
- **Threshold:** Blue channel > Red+Green by 20+ units = blend detected

**Example:**
- White cotton: B=200, G=210, R=205 → 95%+ purity → GOOD
- Blue poly: B=180, G=80, R=70 → 45% purity → BAD

For detailed technical explanation, see the code comments in `fibertrace_demo.py` (classify_item function).

## 🔧 Configuration

You can adjust these values in `fibertrace_demo.py`:

```python
GOOD_ANGLE = 40    # Servo angle for Good bin
BAD_ANGLE  = 140   # Servo angle for Bad bin
CENTER_ANGLE = 90  # Neutral position
```

Adjust these angles based on your physical setup.

##  Troubleshooting

### Camera not working

- **Install camera packages:**
  ```bash
  sudo apt install -y python3-libcamera python3-picamera2 rpicam-apps
  ```
- **Enable camera:**
  ```bash
  sudo raspi-config
  # Interface Options → Camera → Enable
  sudo reboot
  ```
- **Test camera:**
  ```bash
  libcamera-hello -t 0
  vcgencmd get_camera  # Should show: supported=1 detected=1
  ```
- **If OpenCV fails:** The system automatically falls back to `rpicam-jpeg`

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
- Ensure camera and GPIO are working (run `test_hardware.py` first)

### Values not updating in dashboard

- Make sure Flask app is running: `python3 app.py`
- Check that data file exists: `ls fibertrace_data.json`
- Try scanning an item to create/update the data file

##  Project Structure

```
FiberTrace/
├── fibertrace_demo.py    # Main demo script (terminal-based)
├── app.py                 # Flask dashboard server
├── test_hardware.py       # Hardware testing script
├── templates/
│   └── dashboard.html     # Web dashboard UI (industrial design)
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── SETUP.md              # GitHub setup instructions
└── fibertrace_data.json  # Statistics data (created at runtime)
```

##  Web Dashboard Access

Once Flask is running, access the dashboard from:

- **Local (on Pi):** http://localhost:5000
- **Network (other devices):** http://<raspberry-pi-ip>:5000

To find your Pi's IP:
```bash
hostname -I
```

##  Future Enhancements

- Button trigger instead of Enter key
- Automatic conveyor belt detection
- Machine learning model for better classification
- Hyperspectral camera support (900-1700nm wavelength)
- Database storage for historical data
- Email/SMS alerts for low purity
- Modular refactoring (like YVLSWITCH project)
- Real-time video feed option

##  License

This project is open source and available for educational purposes.

##  Credits

Built for automated textile sorting and quality control using Raspberry Pi and computer vision.

**Repository:** https://github.com/AmineBaha-oss/FiberTrace
