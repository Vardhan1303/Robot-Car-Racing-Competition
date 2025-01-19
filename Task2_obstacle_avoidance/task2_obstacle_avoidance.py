import cv2
import numpy as np
from adafruit_rplidar import RPLidar
import RPi.GPIO as GPIO
import time

# GPIO Setup for Motor Control
Motor1_PWM = 18
Motor1_IN1 = 17
Motor1_IN2 = 22
Motor2_PWM = 19
Motor2_IN1 = 4
Motor2_IN2 = 24

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(Motor1_PWM, GPIO.OUT)
GPIO.setup(Motor1_IN1, GPIO.OUT)
GPIO.setup(Motor1_IN2, GPIO.OUT)
GPIO.setup(Motor2_PWM, GPIO.OUT)
GPIO.setup(Motor2_IN1, GPIO.OUT)
GPIO.setup(Motor2_IN2, GPIO.OUT)

pwm1 = GPIO.PWM(Motor1_PWM, 100)
pwm2 = GPIO.PWM(Motor2_PWM, 100)
pwm1.start(0)
pwm2.start(0)

# LiDAR Setup
lidar_port = '/dev/ttyUSB0'
lidar = RPLidar(None, lidar_port)

# Motor control functions
def set_motor_speed(left_speed, right_speed):
    left_speed = max(0, min(100, left_speed * 1.05))
    right_speed = max(0, min(100, right_speed))
    GPIO.output(Motor1_IN1, GPIO.HIGH if left_speed >= 0 else GPIO.LOW)
    GPIO.output(Motor1_IN2, GPIO.LOW if left_speed >= 0 else GPIO.HIGH)
    pwm1.ChangeDutyCycle(abs(left_speed))
    GPIO.output(Motor2_IN1, GPIO.HIGH if right_speed >= 0 else GPIO.LOW)
    GPIO.output(Motor2_IN2, GPIO.LOW if right_speed >= 0 else GPIO.HIGH)
    pwm2.ChangeDutyCycle(abs(right_speed))

def stop_motors():
    GPIO.output(Motor1_IN1, GPIO.LOW)
    GPIO.output(Motor1_IN2, GPIO.LOW)
    GPIO.output(Motor2_IN1, GPIO.LOW)
    GPIO.output(Motor2_IN2, GPIO.LOW)
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)

# Line following module
def follow_line(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    roi = gray[2 * height // 3 :, :]  # Bottom third of the image
    _, binary = cv2.threshold(roi, 60, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            center_x = int(M["m10"] / M["m00"])
            error = center_x - width // 2
            Kp = 0.035
            left_speed = 28 + Kp * error
            right_speed = 28 - Kp * error
            return left_speed, right_speed
    return 0, 0

# LiDAR obstacle detection
def detect_obstacle():
    for scan in lidar.iter_scans(max_buf_meas=500):
        distances = [distance for _, angle, distance in scan if 170 <= angle <= 190]
        if distances:
            return min(distances)
    return float('inf')

# Main control loop
def main_loop():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video stream")
        return

    try:
        lidar.start_motor()
        while True:
            # Line following
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture image")
                break

            left_speed, right_speed = follow_line(frame)

            # Obstacle detection
            distance = detect_obstacle()
            print(f"Distance to obstacle: {distance} mm")

            if distance < 200:  # Stop if closer than 20 cm
                print("Obstacle detected! Stopping.")
                stop_motors()
            else:
                # Continue line following
                set_motor_speed(left_speed, right_speed)

            # Display frame
            cv2.imshow("Frame", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Stopped by user")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        lidar.stop_motor()
        lidar.disconnect()
        stop_motors()
        GPIO.cleanup()

if _name_ == "_main_":
    main_loop()