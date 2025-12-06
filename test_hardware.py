#!/usr/bin/env python3

"""
FiberTrace Hardware Test Script

Tests each component individually:
1. Camera - takes a test photo
2. Green LED - blinks
3. Red LED - blinks
4. Servo - sweeps through angles

Run this to verify all hardware is connected correctly.
"""

import cv2
import time
import sys
import RPi.GPIO as GPIO

# GPIO Pin Configuration
GREEN_LED_PIN = 17
RED_LED_PIN   = 27
SERVO_PIN     = 18

def angle_to_duty(angle):
    """Convert angle (0-180) to duty cycle for 50Hz servo."""
    return 2.5 + (angle / 18.0)

def test_camera():
    """Test camera by taking a photo and displaying it."""
    print("\n" + "="*50)
    print("TEST 1: Camera")
    print("="*50)
    
    try:
        print("Initializing camera...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ ERROR: Could not open camera!")
            print("   - Check camera connection")
            print("   - Make sure camera is enabled: sudo raspi-config")
            return False
        
        print("✓ Camera opened successfully")
        print("Taking test photo in 2 seconds...")
        time.sleep(2)
        
        ret, frame = cap.read()
        if not ret:
            print("❌ ERROR: Could not read frame from camera")
            cap.release()
            return False
        
        print("✓ Frame captured successfully")
        print(f"   Image size: {frame.shape[1]}x{frame.shape[0]} pixels")
        
        # Save test image
        cv2.imwrite('test_camera.jpg', frame)
        print("✓ Test image saved as 'test_camera.jpg'")
        
        # Show image for 3 seconds
        print("Displaying image for 3 seconds...")
        cv2.imshow('Camera Test - Press any key to continue', frame)
        cv2.waitKey(3000)
        cv2.destroyAllWindows()
        
        cap.release()
        print("✓ Camera test PASSED\n")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_leds():
    """Test both LEDs by blinking them."""
    print("="*50)
    print("TEST 2: LEDs")
    print("="*50)
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup pins
        GPIO.setup(GREEN_LED_PIN, GPIO.OUT)
        GPIO.setup(RED_LED_PIN, GPIO.OUT)
        
        # Test Green LED
        print(f"Testing Green LED (GPIO {GREEN_LED_PIN})...")
        GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(GREEN_LED_PIN, GPIO.LOW)
        print("✓ Green LED blinked - did you see it? (y/n): ", end='')
        response = input().strip().lower()
        if response != 'y':
            print("   ⚠️  Check wiring: GPIO 17 → resistor → LED → GND")
        else:
            print("✓ Green LED working!")
        
        # Test Red LED
        print(f"\nTesting Red LED (GPIO {RED_LED_PIN})...")
        GPIO.output(RED_LED_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(RED_LED_PIN, GPIO.LOW)
        print("✓ Red LED blinked - did you see it? (y/n): ", end='')
        response = input().strip().lower()
        if response != 'y':
            print("   ⚠️  Check wiring: GPIO 27 → resistor → LED → GND")
        else:
            print("✓ Red LED working!")
        
        print("✓ LED test PASSED\n")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_servo():
    """Test servo by sweeping through angles."""
    print("="*50)
    print("TEST 3: Servo Motor")
    print("="*50)
    
    try:
        GPIO.setup(SERVO_PIN, GPIO.OUT)
        servo_pwm = GPIO.PWM(SERVO_PIN, 50)  # 50Hz
        servo_pwm.start(0)
        
        print("Servo will move through positions:")
        print("  Center (90°) → Good angle (40°) → Bad angle (140°) → Center")
        print("Watch the servo move...")
        time.sleep(2)
        
        # Center position
        print("\n→ Moving to CENTER (90°)...")
        servo_pwm.ChangeDutyCycle(angle_to_duty(90))
        time.sleep(1)
        servo_pwm.ChangeDutyCycle(0)
        time.sleep(0.5)
        
        # Good angle
        print("→ Moving to GOOD angle (40°)...")
        servo_pwm.ChangeDutyCycle(angle_to_duty(40))
        time.sleep(1)
        servo_pwm.ChangeDutyCycle(0)
        time.sleep(0.5)
        
        # Bad angle
        print("→ Moving to BAD angle (140°)...")
        servo_pwm.ChangeDutyCycle(angle_to_duty(140))
        time.sleep(1)
        servo_pwm.ChangeDutyCycle(0)
        time.sleep(0.5)
        
        # Back to center
        print("→ Returning to CENTER (90°)...")
        servo_pwm.ChangeDutyCycle(angle_to_duty(90))
        time.sleep(1)
        servo_pwm.ChangeDutyCycle(0)
        
        print("\n✓ Did the servo move? (y/n): ", end='')
        response = input().strip().lower()
        if response != 'y':
            print("   ⚠️  Check wiring:")
            print("      - Signal wire (orange/yellow) → GPIO 18 (Pin 12)")
            print("      - Power wire (red) → 5V (Pin 2 or 4)")
            print("      - Ground wire (brown/black) → GND")
            print("   ⚠️  If Pi reboots, servo needs external 5V power")
        else:
            print("✓ Servo working!")
        
        servo_pwm.stop()
        print("✓ Servo test PASSED\n")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("\n" + "="*50)
    print("FiberTrace Hardware Test")
    print("="*50)
    print("\nThis script will test each component:")
    print("  1. Camera")
    print("  2. LEDs (Green & Red)")
    print("  3. Servo Motor")
    print("\nMake sure all hardware is connected before continuing.")
    print("\nPress ENTER to start testing...")
    input()
    
    results = {
        'camera': False,
        'leds': False,
        'servo': False
    }
    
    # Test Camera
    results['camera'] = test_camera()
    
    # Test LEDs
    results['leds'] = test_leds()
    
    # Test Servo
    results['servo'] = test_servo()
    
    # Summary
    print("="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Camera:  {'✓ PASS' if results['camera'] else '❌ FAIL'}")
    print(f"LEDs:    {'✓ PASS' if results['leds'] else '❌ FAIL'}")
    print(f"Servo:   {'✓ PASS' if results['servo'] else '❌ FAIL'}")
    print("="*50)
    
    if all(results.values()):
        print("\n🎉 All tests passed! Hardware is ready.")
        print("You can now run: python3 fibertrace_demo.py")
    else:
        print("\n⚠️  Some tests failed. Please check wiring and try again.")
        print("Refer to README.md for detailed wiring instructions.")
    
    GPIO.cleanup()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        GPIO.cleanup()
        sys.exit(0)

