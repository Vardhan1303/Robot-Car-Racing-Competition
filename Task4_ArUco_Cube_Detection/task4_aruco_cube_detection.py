import cv2
import numpy as np
import RPi.GPIO as GPIO
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# GPIO setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Motor GPIO pin setup
Motor1_PWM = 18
Motor1_IN1 = 17
Motor1_IN2 = 22
Motor2_PWM = 19
Motor2_IN1 = 4
Motor2_IN2 = 24

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

camera_matrix = np.array([
    [640.0, 0.0, 320],
    [0.0, 480, 240],
    [0.0, 0.0, 1.0]
])
dist_coeffs = np.array([0.47355397300107105, -1.5144140141504312, -0.04925321388896157, -0.0005953778540672351, -3.6450646185498092])
aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_50)
parameters = cv2.aruco.DetectorParameters_create()

class KalmanFilter:
    def _init_(self, process_variance, measurement_variance, estimation_error, initial_estimate):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.estimation_error = estimation_error
        self.estimate = initial_estimate

    def update(self, measurement):
        self.estimation_error += self.process_variance
        kalman_gain = self.estimation_error / (self.estimation_error + self.measurement_variance)
        self.estimate += kalman_gain * (measurement - self.estimate)
        self.estimation_error *= (1 - kalman_gain)
        return self.estimate

kalman_filter = KalmanFilter(process_variance=1e-5, measurement_variance=0.1**2, estimation_error=1, initial_estimate=0)

def calculate_distance(tvec):
    return int(tvec[0][0][2] * 100)

def control_robot(distance, desired_distance, lateral_deviation):
    if distance > desired_distance + 5:
        if lateral_deviation > 10:
            left_motor_forward(0.35)
            right_motor_forward(0.25)
        elif lateral_deviation < -10:
            left_motor_forward(0.25)
            right_motor_forward(0.35)
        else:
            left_motor_forward(0.35)
            right_motor_forward(0.3)
    else:
        stop_motors()

def process_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    return corners, ids

def draw_annotations(frame, corners, ids, distances, fps):
    if ids is not None:
        for i, corner in enumerate(corners):
            marker_id = ids[i][0]
            int_corners = np.int0(corner)
            cv2.polylines(frame, [int_corners], True, (0, 255, 0), 2)
            center = tuple(np.mean(corner[0], axis=0).astype(int))
            cv2.circle(frame, center, 5, (0, 0, 255), -1)
            distance = distances.get(marker_id, "N/A")
            cv2.putText(frame, f"ID: {marker_id} Dist: {distance} cm", (center[0], center[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.putText(frame, f"ID 0: {distances.get(0, 'Not detected')} cm", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"ID 1: {distances.get(1, 'Not detected')} cm", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    else:
        cv2.putText(frame, "No ArUco detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"FPS: {fps:.2f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return frame

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            logging.error("Failed to capture frame")
            break

        corners, ids = process_frame(frame)
        distances = {}
        if ids is not None:
            for i, marker_id in enumerate(ids.flatten()):
                rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(corners[i], 0.05, camera_matrix, dist_coeffs)
                distance = calculate_distance(tvec)
                distances[marker_id] = distance
                lateral_deviation = kalman_filter.update(tvec[0][0][0])
                if marker_id == 0:
                    control_robot(distance, 20, lateral_deviation)
                elif marker_id == 1:
                    control_robot(distance, 40, lateral_deviation)
        else:
            stop_motors()

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame = draw_annotations(frame, corners, ids, distances, fps)
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