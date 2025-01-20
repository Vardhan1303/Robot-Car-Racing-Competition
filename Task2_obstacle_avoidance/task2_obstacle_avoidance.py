import cv2
import numpy as np
import RPi.GPIO as GPIO
import time
from adafruit_rplidar import RPLidar
from threading import Thread, Lock

# GPIO Setup
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

# Global variables for thread synchronization
lidar_data = {'front': float('inf'), 'left': float('inf'), 'right': float('inf')}
lidar_lock = Lock()
obstacle_detected = False  # Flag to control stopping behavior

# Set FPS target for the main loop
target_fps = 30
frame_time = 1.0 / target_fps

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

# LiDAR Setup
lidar_port = '/dev/ttyUSB0'
lidar = RPLidar(None, lidar_port)

def lidar_thread():
    global lidar_data
    while True:
        try:
            lidar.connect()
            lidar.start_motor()
            for scan in lidar.iter_scans(max_buf_meas=600):  # Reduce the number of measurements
                with lidar_lock:
                    front_distances = [distance for quality, angle, distance in scan if 150 <= angle <= 210]
                    left_distances = [distance for quality, angle, distance in scan if 90 <= angle <= 110]
                    right_distances = [distance for quality, angle, distance in scan if 250 <= angle <= 270]

                    if front_distances:
                        lidar_data['front'] = min(front_distances)
                    if left_distances:
                        lidar_data['left'] = min(left_distances)
                    if right_distances:
                        lidar_data['right'] = min(right_distances)

        except Exception as e:
            print(f"LiDAR Error in thread: {e}")
        finally:
            try:
                lidar.stop()
                lidar.disconnect()
            except Exception as e:
                print(f"LiDAR Disconnection Error: {e}")

def main_loop():
    global obstacle_detected
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open video stream")
        return

    lidar_thread_instance = Thread(target=lidar_thread, daemon=True)
    lidar_thread_instance.start()

    try:
        while True:
            # Capture frame and limit FPS
            start_time = time.time()

            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture image")
                break

            # Resize frame to reduce computation load (you can adjust size as needed)
            frame = cv2.resize(frame, (640, 480))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            roi_start = 2 * height // 3
            roi = gray[roi_start:, :]

            _, binary = cv2.threshold(roi, 60, 255, cv2.THRESH_BINARY_INV)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            result_image = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

            center_x = center_y = None
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    center_x = int(M["m10"] / M["m00"])
                    center_y = int(M["m01"] / M["m00"])
                    cv2.circle(result_image, (center_x, center_y), 5, (0, 255, 0), -1)  # Green

            error = (center_x - width // 2) if center_x is not None else 0
            Kp = 0.035
            left_speed = 28 + Kp * error
            right_speed = 28 - Kp * error

            # LiDAR Processing
            with lidar_lock:
                front_distance = lidar_data['front']
            
            print(f"Front Distance: {front_distance} mm")
            
            # Stop robot if an obstacle is detected within 20 cm (200 mm)
            if front_distance < 500:  # 200 mm = 20 cm
                if not obstacle_detected:
                    stop_motors()  # Stop the motors
                    obstacle_detected = True
                    print("Obstacle detected in front! Stopping.")
            else:
                if obstacle_detected:
                    # If we were stopping due to obstacle, resume movement
                    obstacle_detected = False
                set_motor_speed(left_speed, right_speed)
                print(f"Moving with left speed: {left_speed}, right speed: {right_speed}")

            cv2.imshow("Binary Image", binary)
            cv2.imshow("Track Markings", result_image)

            # Control the FPS rate to maintain smooth operation
            end_time = time.time()
            elapsed_time = end_time - start_time
            time_to_wait = frame_time - elapsed_time
            if time_to_wait > 0:
                time.sleep(time_to_wait)

            if cv2.waitKey(1) & 0xFF == ord('s'):
                break

    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        print("Cleaning up...")
        cap.release()
        cv2.destroyAllWindows()
        stop_motors()
        try:
            lidar.stop()
            lidar.disconnect()
        except Exception as e:
            print(f"LiDAR Cleanup Error: {e}")
        GPIO.cleanup()
        print("Motors stopped and GPIO cleaned up.")

main_loop()