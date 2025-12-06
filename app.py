#!/usr/bin/env python3

"""
FiberTrace Flask Dashboard

Web-based dashboard to monitor bale purity statistics in real-time.
Access at: http://raspberry-pi-ip:5000
"""

from flask import Flask, render_template, jsonify, request, Response
import json
import os
import time
import cv2
import subprocess
from datetime import datetime

import RPi.GPIO as GPIO

# Import camera functions from demo script
try:
    from fibertrace_demo import init_camera, get_frame, classify_item, save_data, load_data, setup_gpio, move_gate, angle_to_duty
except ImportError:
    # Fallback if import fails
    print("⚠️  Could not import from fibertrace_demo.py, some functions may not work")

app = Flask(__name__)

DATA_FILE = "fibertrace_data.json"
CAMERA_IMAGE_FILE = "camera_preview.jpg"
GREEN_LED_PIN = 17
RED_LED_PIN = 27
SERVO_PIN = 18
GOOD_ANGLE = 40
BAD_ANGLE = 140
CENTER_ANGLE = 90

# Global camera and GPIO state
camera_cap = None
servo_pwm = None
gpio_setup = False

def init_flask_hardware():
    """Initialize camera and GPIO for Flask app."""
    global camera_cap, servo_pwm, gpio_setup
    
    if not gpio_setup:
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(GREEN_LED_PIN, GPIO.OUT)
            GPIO.setup(RED_LED_PIN, GPIO.OUT)
            GPIO.setup(SERVO_PIN, GPIO.OUT)
            GPIO.output(GREEN_LED_PIN, GPIO.LOW)
            GPIO.output(RED_LED_PIN, GPIO.LOW)
            
            servo_pwm = GPIO.PWM(SERVO_PIN, 50)
            servo_pwm.start(angle_to_duty(CENTER_ANGLE))
            time.sleep(0.5)
            servo_pwm.ChangeDutyCycle(0)
            gpio_setup = True
            print("✓ GPIO initialized for Flask")
        except Exception as e:
            print(f"⚠️  GPIO init warning: {e}")
    
    if camera_cap is None:
        try:
            camera_cap = init_camera()
            print("✓ Camera initialized for Flask")
        except Exception as e:
            print(f"⚠️  Camera init warning: {e}")

def angle_to_duty(angle):
    """Convert angle to duty cycle for servo."""
    return 2.5 + (angle / 18.0)

def move_gate(angle, servo_pwm):
    """Move servo gate to specific angle."""
    duty = angle_to_duty(angle)
    servo_pwm.ChangeDutyCycle(duty)
    time.sleep(0.4)
    servo_pwm.ChangeDutyCycle(0)

def perform_scan():
    """Perform a scan and update statistics."""
    global camera_cap, servo_pwm
    
    try:
        # Get frame
        frame = get_frame(camera_cap)
        if frame is None:
            return {"success": False, "error": "Could not capture frame"}
        
        # Save preview image
        cv2.imwrite(CAMERA_IMAGE_FILE, frame)
        
        # Classify
        result = classify_item(frame)
        
        # Load current data
        data = load_data()
        data['total_scanned'] = data.get('total_scanned', 0) + 1
        
        if result == "GOOD":
            data['good_count'] = data.get('good_count', 0) + 1
            # Control hardware
            GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
            GPIO.output(RED_LED_PIN, GPIO.LOW)
            if servo_pwm:
                move_gate(GOOD_ANGLE, servo_pwm)
        else:
            data['bad_count'] = data.get('bad_count', 0) + 1
            # Control hardware
            GPIO.output(GREEN_LED_PIN, GPIO.LOW)
            GPIO.output(RED_LED_PIN, GPIO.HIGH)
            if servo_pwm:
                move_gate(BAD_ANGLE, servo_pwm)
        
        data['last_update'] = time.time()
        data['last_result'] = result
        
        # Save data
        save_data()
        
        # Reset after 1 second
        time.sleep(1.0)
        GPIO.output(GREEN_LED_PIN, GPIO.LOW)
        GPIO.output(RED_LED_PIN, GPIO.LOW)
        if servo_pwm:
            move_gate(CENTER_ANGLE, servo_pwm)
        
        return {"success": True, "result": result, "data": data}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    """API endpoint to get current statistics."""
    data = load_data()
    
    total = data.get('total_scanned', 0)
    good = data.get('good_count', 0)
    bad = data.get('bad_count', 0)
    
    if total > 0:
        purity = (good / total) * 100.0
    else:
        purity = 0.0
    
    last_update = data.get('last_update', 0)
    if last_update > 0:
        last_update_str = datetime.fromtimestamp(last_update).strftime('%Y-%m-%d %H:%M:%S')
    else:
        last_update_str = "Never"
    
    return jsonify({
        'total_scanned': total,
        'good_count': good,
        'bad_count': bad,
        'purity': round(purity, 1),
        'last_update': last_update_str,
        'last_result': data.get('last_result', 'N/A')
    })

@app.route('/api/camera/preview')
def camera_preview():
    """Get latest camera preview image."""
    global camera_cap
    try:
        frame = get_frame(camera_cap)
        if frame is not None:
            cv2.imwrite(CAMERA_IMAGE_FILE, frame)
            with open(CAMERA_IMAGE_FILE, 'rb') as f:
                image_data = f.read()
            return Response(image_data, mimetype='image/jpeg')
        else:
            return Response("Camera not available", status=503)
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)

@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """Trigger a scan from the web interface."""
    init_flask_hardware()
    result = perform_scan()
    return jsonify(result)

if __name__ == '__main__':
    print("Starting FiberTrace Dashboard...")
    print("Access at: http://localhost:5000")
    print("Or from another device: http://<raspberry-pi-ip>:5000")
    
    # Initialize hardware
    try:
        init_flask_hardware()
    except Exception as e:
        print(f"⚠️  Hardware initialization warning: {e}")
        print("   Some features may not work, but dashboard will still run.")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

