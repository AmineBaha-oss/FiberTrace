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
import subprocess

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
                if data is None:
                    return {
                        'total_scanned': 0,
                        'good_count': 0,
                        'bad_count': 0,
                        'last_update': 0
                    }
                total_scanned = data.get('total_scanned', 0)
                good_count = data.get('good_count', 0)
                bad_count = data.get('bad_count', 0)
                return data
        except:
            pass  # If file is corrupted, start fresh
    
    # Return default if file doesn't exist or load failed
    return {
        'total_scanned': 0,
        'good_count': 0,
        'bad_count': 0,
        'last_update': 0
    }

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
    Returns cap object (may be None if OpenCV fails - we'll use rpicam-jpeg fallback).
    """
    cap = None
    
    # Try OpenCV first
    try:
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            # Test if we can actually read a frame
            ret, frame = cap.read()
            if ret and frame is not None:
                print("✓ Camera initialized with OpenCV")
                return cap
            else:
                cap.release()
                cap = None
    except:
        if cap:
            cap.release()
        cap = None
    
    # If OpenCV failed, we'll use rpicam-jpeg fallback
    if cap is None:
        print("⚠️  OpenCV cannot access camera, will use rpicam-jpeg fallback")
    
    return cap  # May be None - that's OK, we have fallback

def capture_frame_fallback(path="frame.jpg"):
    """
    Fallback: Use rpicam-jpeg to capture a single frame.
    Works on Raspberry Pi OS Bookworm when OpenCV can't access /dev/video0.
    """
    import subprocess
    try:
        # Take 1 snapshot with the Pi camera (1000ms timeout)
        cmd = ["rpicam-jpeg", "-o", path, "-t", "1000"]
        subprocess.run(cmd, check=True, capture_output=True, timeout=5)
        img = cv2.imread(path)
        if img is not None:
            return img
        else:
            print("ERROR: Could not read image from rpicam-jpeg")
            return None
    except subprocess.CalledProcessError as e:
        print(f"ERROR: rpicam-jpeg failed: {e}")
        return None
    except FileNotFoundError:
        print("ERROR: rpicam-jpeg not found. Install: sudo apt install -y rpicam-apps")
        return None
    except Exception as e:
        print(f"ERROR: rpicam-jpeg exception: {e}")
        return None

def get_frame(cap):
    """
    Get a frame from camera. Tries OpenCV first, falls back to rpicam-jpeg if needed.
    """
    if cap is not None and cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            return frame
    
    # Fallback if cap is None or OpenCV failed
    return capture_frame_fallback()

def classify_item(frame):
    """
    Classify the item and calculate purity percentage.
    Returns: dict with 'result' (GOOD/BAD), 'purity' (0-100%), and 'composition'
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
    
    # Calculate color ratios
    total = mean_b + mean_g + mean_r
    if total > 0:
        blue_ratio = mean_b / total
        green_ratio = mean_g / total
        red_ratio = mean_r / total
    else:
        blue_ratio = green_ratio = red_ratio = 0.33
    
    # Calculate purity percentage
    # White/light colors (high red+green, low blue) = high cotton purity
    # Blue colors = poly blend contamination
    # Purity is based on how "white" vs "blue" the item is
    cotton_purity = (red_ratio + green_ratio) * 100  # Higher red+green = more cotton-like
    poly_contamination = blue_ratio * 100  # Higher blue = more poly blend
    
    # Determine if it's GOOD (pure cotton) or BAD (blend)
    # Threshold: if blue is significantly dominant, it's a blend
    blue_dominant = (mean_b > mean_g + 20) and (mean_b > mean_r + 20)
    
    # For debugging: print color values
    print(f"DEBUG: mean BGR = ({mean_b:.1f}, {mean_g:.1f}, {mean_r:.1f})")
    print(f"DEBUG: Cotton purity = {cotton_purity:.1f}%, Poly contamination = {poly_contamination:.1f}%")
    
    if blue_dominant:
        result = "BAD"
        # For blends, show the contamination percentage
        purity = max(0, 100 - poly_contamination)
        composition = f"{purity:.0f}% Cotton, {poly_contamination:.0f}% Poly Blend"
    else:
        result = "GOOD"
        # For pure cotton, show high purity
        purity = min(100, cotton_purity + 10)  # Add small buffer for pure white
        if purity >= 98:
            composition = "100% Pure Cotton"
        else:
            composition = f"{purity:.0f}% Cotton"
    
    return {
        'result': result,
        'purity': round(purity, 1),
        'composition': composition,
        'cotton_pct': round(cotton_purity, 1),
        'poly_pct': round(poly_contamination, 1)
    }

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
            
            # Read a single frame (uses OpenCV or rpicam-jpeg fallback)
            frame = get_frame(cap)
            if frame is None:
                print("WARNING: Could not read frame from camera.")
                continue
            
            # Optional: show the frame in a small window for debugging
            # cv2.imshow("Scanner View", frame)
            # cv2.waitKey(1)
            
            # Classify
            classification = classify_item(frame)
            result = classification['result']
            purity = classification['purity']
            composition = classification['composition']
            
            total_scanned += 1
            
            if result == "GOOD":
                good_count += 1
                print(f"RESULT: GOOD - {composition} (Purity: {purity}%)")
                GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
                GPIO.output(RED_LED_PIN, GPIO.LOW)
                move_gate(GOOD_ANGLE, servo_pwm)
            else:
                bad_count += 1
                print(f"RESULT: BAD - {composition} (Purity: {purity}%)")
                GPIO.output(GREEN_LED_PIN, GPIO.LOW)
                GPIO.output(RED_LED_PIN, GPIO.HIGH)
                move_gate(BAD_ANGLE, servo_pwm)
            
            # Save data for Flask dashboard (include item purity)
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
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

