import cv2
import RPi.GPIO as GPIO

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
    roi = gray[2 * height // 3 :, :]  # Region of Interest (bottom third of the frame)
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
            return left_speed, right_speed, roi, binary
    return 0, 0, roi, binary

# Main control loop for Line Following
def main_loop():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video stream")
        return

    no_line_frames = 0  # Counter to stop motors after a few frames with no line detection

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture image")
                break

            # Line following logic
            left_speed, right_speed, roi, binary = follow_line(frame)

            # If no line is detected for several frames, stop the robot
            if left_speed == 0 and right_speed == 0:
                no_line_frames += 1
                if no_line_frames > 50:  # Stop after 50 frames with no line detection
                    stop_motors()
                    print("No line detected. Stopping robot.")
                    continue
            else:
                no_line_frames = 0  # Reset counter if line is detected

            # Control motors based on line-following logic
            set_motor_speed(left_speed, right_speed)

            # Show the ROI and the binary thresholded image
            cv2.imshow("ROI", roi)  # Show the region of interest (ROI)
            cv2.imshow("Binary Image", binary)  # Show the binary image after thresholding
            cv2.imshow("Frame", frame)  # Show the original frame

            # Exit if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('s'):
                break

    except Exception as e:
        print(f"Error: {e}")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        stop_motors()
        GPIO.cleanup()

if __name__ == "__main__":
    main_loop()