import cv2
import RPi.GPIO as GPIO
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# GPIO pin setup for motor control
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Define motor pins
Motor1_PWM = 18
Motor1_IN1 = 17
Motor1_IN2 = 22
Motor2_PWM = 19
Motor2_IN1 = 4
Motor2_IN2 = 24

# Set up GPIO pins for motors
GPIO.setup(Motor1_PWM, GPIO.OUT)
GPIO.setup(Motor1_IN1, GPIO.OUT)
GPIO.setup(Motor1_IN2, GPIO.OUT)
GPIO.setup(Motor2_PWM, GPIO.OUT)
GPIO.setup(Motor2_IN1, GPIO.OUT)
GPIO.setup(Motor2_IN2, GPIO.OUT)

# Initialize PWM for motors
pwm_motor1 = GPIO.PWM(Motor1_PWM, 100)
pwm_motor2 = GPIO.PWM(Motor2_PWM, 100)
pwm_motor1.start(0)
pwm_motor2.start(0)

# Function to stop the motors
def stop():
    GPIO.output(Motor1_IN1, GPIO.LOW)
    GPIO.output(Motor1_IN2, GPIO.LOW)
    GPIO.output(Motor2_IN1, GPIO.LOW)
    GPIO.output(Motor2_IN2, GPIO.LOW)
    pwm_motor1.ChangeDutyCycle(0)
    pwm_motor2.ChangeDutyCycle(0)
    logging.info("Motors stopped.")

# Function to control motor speed
def set_motor_speed(left_speed, right_speed):
    left_speed = max(0, min(100, left_speed))
    right_speed = max(0, min(100, right_speed))
    pwm_motor1.ChangeDutyCycle(left_speed)
    pwm_motor2.ChangeDutyCycle(right_speed)
    logging.info(f"Motor speeds set - Left: {left_speed}%, Right: {right_speed}%")

# Function to move forward
def forward(base_speed, error, Kp):
    left_speed = base_speed - (Kp * error)
    right_speed = base_speed + (Kp * error)

    # Control motor directions for forward movement
    GPIO.output(Motor1_IN1, GPIO.HIGH)
    GPIO.output(Motor1_IN2, GPIO.LOW)
    GPIO.output(Motor2_IN1, GPIO.HIGH)
    GPIO.output(Motor2_IN2, GPIO.LOW)

    # Set motor speeds
    set_motor_speed(left_speed, right_speed)

# Main function for line following
def line_follower():
    try:
        # Initialize camera
        camera = cv2.VideoCapture(0)  # Adjust camera ID if necessary
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        time.sleep(2)  # Allow the camera to stabilize

        Kp = 0.05  # Proportional gain for steering
        base_speed = 20  # Base motor speed
        logging.info("Line follower started.")

        previous_center_x = None  # To dynamically adjust ROI

        while True:
            # Capture a frame from the camera
            ret, frame = camera.read()
            if not ret:
                logging.error("Failed to grab frame.")
                break

            # Convert frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Dynamically define ROI based on previous frame
            height, width = gray.shape
            roi_start = 2 * height // 3 if previous_center_x is None else max(0, previous_center_x - 50)
            roi = gray[roi_start:, :]

            # Preprocessing
            roi = cv2.GaussianBlur(roi, (5, 5), 0)

            # Adaptive Thresholding
            binary = cv2.adaptiveThreshold(
                roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )

            # Morphological Operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            # Edge Detection (optional for better line localization)
            edges = cv2.Canny(binary, 50, 150)

            # Find contours in the binary image
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Initialize variables
            center_x = None
            if contours:
                # Select the largest contour (assume it's the line)
                largest_contour = max(contours, key=cv2.contourArea)
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    # Calculate the centroid of the line
                    center_x = int(M["m10"] / M["m00"])
                    # Draw the detected line center for debugging
                    cv2.circle(roi, (center_x, roi.shape[0] // 2), 5, (255, 0, 0), -1)

            # Calculate the error (deviation from center)
            error = center_x - (width // 2) if center_x is not None else 0

            # Adjust motor speeds based on error
            forward(base_speed, error, Kp)

            # Update previous center
            if center_x is not None:
                previous_center_x = center_x

            # Display the binary image and ROI (for debugging)
            cv2.imshow("Binary Image", binary)
            cv2.imshow("ROI", roi)

            # Break loop on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        logging.info("Line following stopped by user.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        # Clean up
        stop()
        GPIO.cleanup()
        camera.release()
        cv2.destroyAllWindows()
        logging.info("Cleaned up and exited.")

# Run the line follower
line_follower()