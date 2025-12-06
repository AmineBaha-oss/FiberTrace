#!/usr/bin/env python3

"""
FiberTrace Conveyor Demo Prototype

- White paper  -> GOOD (cotton)  -> green LED, gate to Good bin
- Blue paper   -> BAD (blend)    -> red LED, gate to Bad bin

Controls:
- Place either white or blue paper under the camera (scanner box).
- Press ENTER in the terminal to trigger a scan.
- Watch LEDs, servo gate, and text "dashboard" update.
"""

import cv2
import time
import sys
import RPi.GPIO as GPIO
import json
import os

# ------------------------
# GPIO PIN CONFIG
# ------------------------
GREEN_LED_PIN = 17
RED_LED_PIN   = 27
SERVO_PIN     = 18

# Servo angles (in degrees) for Good vs Bad
GOOD_ANGLE = 40    # adjust to point at "Good Bale" box
BAD_ANGLE  = 140   # adjust to point at "Bad Bale" box
CENTER_ANGLE = 90  # neutral/resting position

# Data file for Flask dashboard
DATA_FILE = "fibertrace_data.json"

# ------------------------
# GLOBAL STATE
# ------------------------
total_scanned = 0
good_count    = 0
bad_count     = 0

# ------------------------
# DATA PERSISTENCE
# ------------------------
def load_data():
    """Load statistics from JSON file."""
    global total_scanned, good_count, bad_count
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                total_scanned = data.get('total_scanned', 0)
                good_count = data.get('good_count', 0)
                bad_count = data.get('bad_count', 0)
        except:
            pass  # If file is corrupted, start fresh

def save_data():
    """Save statistics to JSON file for Flask dashboard."""
    data = {
        'total_scanned': total_scanned,
        'good_count': good_count,
        'bad_count': bad_count,
        'last_update': time.time()
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# ------------------------
# SERVO HELPER
# ------------------------
def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # LEDs
    GPIO.setup(GREEN_LED_PIN, GPIO.OUT)
    GPIO.setup(RED_LED_PIN, GPIO.OUT)
    
    # Turn both off at start
    GPIO.output(GREEN_LED_PIN, GPIO.LOW)
    GPIO.output(RED_LED_PIN, GPIO.LOW)
    
    # Servo
    GPIO.setup(SERVO_PIN, GPIO.OUT)

def angle_to_duty(angle):
    """
    Convert angle (0-180) to duty cycle for standard 50Hz servo.
    0 deg  -> ~2.5% duty
    180 deg-> ~12.5% duty
    """
    return 2.5 + (angle / 18.0)

def move_gate(angle, servo_pwm):
    """
    Move servo gate to specific angle.
    """
    duty = angle_to_duty(angle)
    servo_pwm.ChangeDutyCycle(duty)
    time.sleep(0.4)   # small delay to let servo move
    # Optional: stop sending pulses to reduce jitter
    servo_pwm.ChangeDutyCycle(0)

# ------------------------
# CAMERA + COLOR LOGIC
# ------------------------
def init_camera(camera_index=0):
    """
    Initialize the camera using OpenCV.
    Tries multiple methods for compatibility with different Pi OS versions.
    """
    cap = None
    
    # Method 1: Try libcamera with v4l2 backend (newer Pi OS)
    try:
        cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            ret, frame = cap.read()
            if ret and frame is not None:
                return cap
            else:
                cap.release()
                cap = None
    except:
        if cap:
            cap.release()
        cap = None
    
    # Method 2: Try standard initialization
    if cap is None:
        try:
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                ret, frame = cap.read()
                if ret and frame is not None:
                    return cap
                else:
                    cap.release()
                    cap = None
        except:
            if cap:
                cap.release()
            cap = None
    
    # Method 3: Try camera index 1
    if cap is None and camera_index == 0:
        try:
            cap = cv2.VideoCapture(1)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    return cap
                else:
                    cap.release()
                    cap = None
        except:
            if cap:
                cap.release()
            cap = None
    
    if cap is None or not cap.isOpened():
        print("ERROR: Could not open camera. Check connection and index.")
        print("Troubleshooting:")
        print("  1. Enable camera: sudo raspi-config → Interface Options → Camera")
        print("  2. Reboot: sudo reboot")
        print("  3. Check camera: vcgencmd get_camera")
        sys.exit(1)
    
    return cap

def classify_item(frame):
    """
    Classify the item under the camera as GOOD (white) or BAD (blue).
    Very simple color-based check for demo purposes.
    Returns: "GOOD" or "BAD"
    """
    # Use a central crop region of interest (ROI)
    h, w, _ = frame.shape
    cx, cy = w // 2, h // 2
    box_size = min(w, h) // 4
    
    x1 = cx - box_size
    x2 = cx + box_size
    y1 = cy - box_size
    y2 = cy + box_size
    
    roi = frame[y1:y2, x1:x2]
    
    # Compute average color in ROI (BGR)
    mean_color = roi.mean(axis=0).mean(axis=0)
    mean_b, mean_g, mean_r = mean_color
    
    # Decide: simple logic
    # If blue channel significantly higher than red & green -> BAD (blue paper)
    # Else -> GOOD (white/light paper)
    blue_dominant = (mean_b > mean_g + 20) and (mean_b > mean_r + 20)
    
    # For debugging: print color values
    print(f"DEBUG: mean BGR = ({mean_b:.1f}, {mean_g:.1f}, {mean_r:.1f})")
    
    if blue_dominant:
        return "BAD"
    else:
        return "GOOD"

# ------------------------
# DASHBOARD PRINTING
# ------------------------
def print_dashboard():
    if total_scanned == 0:
        purity = 0.0
    else:
        purity = (good_count / total_scanned) * 100.0
    
    print("\n================ FiberTrace Demo Dashboard ================")
    print(f" Total items scanned : {total_scanned}")
    print(f" Good (cotton)       : {good_count}")
    print(f" Bad (poly-blend)    : {bad_count}")
    print(f" Bale purity         : {purity:.1f}%")
    print("===========================================================\n")

# ------------------------
# MAIN LOOP
# ------------------------
def main():
    global total_scanned, good_count, bad_count
    
    # Load existing data
    load_data()
    
    print("Setting up GPIO...")
    setup_gpio()
    
    print("Initializing servo PWM on pin", SERVO_PIN)
    servo_pwm = GPIO.PWM(SERVO_PIN, 50)  # 50Hz
    servo_pwm.start(angle_to_duty(CENTER_ANGLE))
    time.sleep(0.5)
    servo_pwm.ChangeDutyCycle(0)  # stop pulses for now
    
    print("Initializing camera...")
    cap = init_camera(camera_index=0)
    
    print("\nFiberTrace Conveyor Demo Ready.")
    print("Instructions:")
    print(" 1) Place WHITE or BLUE paper under the camera.")
    print(" 2) Press ENTER to scan the item.")
    print(" 3) Watch LEDs, servo gate, and terminal dashboard.\n")
    print("Press CTRL+C to quit.\n")
    
    try:
        while True:
            input(">>> Press ENTER to SCAN the current item...")
            
            # Read a single frame
            ret, frame = cap.read()
            if not ret:
                print("WARNING: Could not read frame from camera.")
                continue
            
            # Optional: show the frame in a small window for debugging
            # cv2.imshow("Scanner View", frame)
            # cv2.waitKey(1)
            
            # Classify
            result = classify_item(frame)
            total_scanned += 1
            
            if result == "GOOD":
                good_count += 1
                print("RESULT: GOOD (cotton / pure bale)")
                GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
                GPIO.output(RED_LED_PIN, GPIO.LOW)
                move_gate(GOOD_ANGLE, servo_pwm)
            else:
                bad_count += 1
                print("RESULT: BAD (poly-blend / contamination)")
                GPIO.output(GREEN_LED_PIN, GPIO.LOW)
                GPIO.output(RED_LED_PIN, GPIO.HIGH)
                move_gate(BAD_ANGLE, servo_pwm)
            
            # Save data for Flask dashboard
            save_data()
            print_dashboard()
            
            # Small delay, then turn off LEDs and center gate if you want
            time.sleep(1.0)
            GPIO.output(GREEN_LED_PIN, GPIO.LOW)
            GPIO.output(RED_LED_PIN, GPIO.LOW)
            move_gate(CENTER_ANGLE, servo_pwm)
            
    except KeyboardInterrupt:
        print("\nExiting demo...")
    finally:
        print("Cleaning up GPIO and camera...")
        servo_pwm.stop()
        GPIO.cleanup()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

