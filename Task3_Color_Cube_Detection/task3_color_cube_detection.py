import cv2
import numpy as np
import time
import RPi.GPIO as GPIO
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# GPIO setup (Motor control)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

Motor1_PWM = 18
Motor1_IN1 = 17
Motor1_IN2 = 22

Motor2_PWM = 19
Motor2_IN1 = 4
Motor2_IN2 = 24

# Motor PWM setup
GPIO.setup(Motor1_PWM, GPIO.OUT)
GPIO.setup(Motor1_IN1, GPIO.OUT)
GPIO.setup(Motor1_IN2, GPIO.OUT)

GPIO.setup(Motor2_PWM, GPIO.OUT)
GPIO.setup(Motor2_IN1, GPIO.OUT)
GPIO.setup(Motor2_IN2, GPIO.OUT)

motor1_pwm = GPIO.PWM(Motor1_PWM, 100)
motor2_pwm = GPIO.PWM(Motor2_PWM, 100)

motor1_pwm.start(0)
motor2_pwm.start(0)

# Motor control functions
def left_motor_forward(speed):
    GPIO.output(Motor1_IN1, GPIO.HIGH)
    GPIO.output(Motor1_IN2, GPIO.LOW)
    motor1_pwm.ChangeDutyCycle(speed * 100)

def right_motor_forward(speed):
    GPIO.output(Motor2_IN1, GPIO.HIGH)
    GPIO.output(Motor2_IN2, GPIO.LOW)
    motor2_pwm.ChangeDutyCycle(speed * 100)

def left_motor_backward(speed):
    GPIO.output(Motor1_IN1, GPIO.LOW)
    GPIO.output(Motor1_IN2, GPIO.HIGH)
    motor1_pwm.ChangeDutyCycle(speed * 100)

def right_motor_backward(speed):
    GPIO.output(Motor2_IN1, GPIO.LOW)
    GPIO.output(Motor2_IN2, GPIO.HIGH)
    motor2_pwm.ChangeDutyCycle(speed * 100)

def stop_motors():
    motor1_pwm.ChangeDutyCycle(0)
    motor2_pwm.ChangeDutyCycle(0)
    GPIO.output(Motor1_IN1, GPIO.LOW)
    GPIO.output(Motor1_IN2, GPIO.LOW)
    GPIO.output(Motor2_IN1, GPIO.LOW)
    GPIO.output(Motor2_IN2, GPIO.LOW)

def control_robot(distance, desired_distance, lateral_deviation):
    if distance > desired_distance + 2:
        if lateral_deviation > 5:
            left_motor_forward(0.35)
            right_motor_forward(0.25)
        elif lateral_deviation < -5:
            left_motor_forward(0.25)
            right_motor_forward(0.35)
        else:
            left_motor_forward(0.25)
            right_motor_forward(0.2)
    else:
        stop_motors()

# Color detection
def detect_cube(frame, color='red'):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    if color == 'red':
        lower_red1 = np.array([0, 120, 70])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 120, 70])
        upper_red2 = np.array([180, 255, 255])
        mask = cv2.bitwise_or(cv2.inRange(hsv, lower_red1, upper_red1), cv2.inRange(hsv, lower_red2, upper_red2))
    elif color == 'green':
        lower_green = np.array([35, 50, 50])
        upper_green = np.array([85, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_green)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def estimate_distance(cube_area):
    focal_length = 640
    known_size = 2.5
    if cube_area > 0:
        return (focal_length * known_size) / np.sqrt(cube_area)
    return float('inf')

try:
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    while True:
        ret, frame = cap.read()
        if not ret:
            logging.error("Failed to capture frame")
            break
        
        red_contours = detect_cube(frame, 'red')
        green_contours = detect_cube(frame, 'green')
        
        target_color = None
        target_distance = None
        target_deviation = None
        
        if red_contours:
            largest_red = max(red_contours, key=cv2.contourArea)
            red_area = cv2.contourArea(largest_red)
            red_distance = estimate_distance(red_area)
            x, y, w, h = cv2.boundingRect(largest_red)
            cx = x + w // 2
            target_color = 'red'
            target_distance = red_distance
            target_deviation = cx - 320
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
            #cv2.putText(frame, f"Red: {red_distance:.2f} cm", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if green_contours:
            largest_green = max(green_contours, key=cv2.contourArea)
            green_area = cv2.contourArea(largest_green)
            green_distance = estimate_distance(green_area)
            x, y, w, h = cv2.boundingRect(largest_green)
            cx = x + w // 2
            target_color = 'green'
            target_distance = green_distance
            target_deviation = cx - 320
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            #cv2.putText(frame, f"Green: {green_distance:.2f} cm", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if target_color == 'red':
            control_robot(target_distance, 45, target_deviation)
        elif target_color == 'green':
            control_robot(target_distance, 25, target_deviation)
        else:
            stop_motors()
        
        cv2.imshow('Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    logging.info("Interrupted by user")
finally:
    cap.release()
    cv2.destroyAllWindows()
    stop_motors()
    GPIO.cleanup()