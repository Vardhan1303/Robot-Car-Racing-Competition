# 🟥🟩 Cube-Tracking Robot with Raspberry Pi

This project involves a Raspberry Pi-powered robot capable of identifying, tracking, and stopping at red and green cubes. The robot uses a camera for vision, GPIO for motor control, and OpenCV for image processing. It demonstrates color-based object tracking and dynamic distance-based stopping behavior.

---

## 📋 Table of Contents
- [Overview](#overview)  
- [Features](#features)  
- [Setup and Execution](#setup-and-execution)  
- [How It Works](#how-it-works)  
- [Results](#results)  
- [License](#license)  

---

## 📝 Overview

The robot is programmed to:
1. Detect red and green cubes using a camera.
2. Move toward the cube that is closest.
3. Stop **40 cm** in front of a red cube and **20 cm** in front of a green cube.
4. Remain stationary when no cube is visible.

---

## 🌟 Features

- Real-time detection of red and green cubes using OpenCV.
- Distance estimation from the cube based on its area in the frame.
- Prioritizes movement toward the closest cube when both are visible.
- Stops dynamically at predefined distances based on cube color.
- Modular and reusable motor control functions.

---

## 🚀 Setup and Execution

1. **Hardware Assembly**: Connect the motors, camera, and motor driver to the Raspberry Pi as per the wiring diagram.
2. **Clone the Repository**
3. **Run the Script**
4. **Test the Robot**:  
   - Place the red and green cubes at various distances.
   - Observe the robot's ability to move toward the cubes and stop at the correct distance.

---

## ⚙️ How It Works

### **Cube Detection**
- **Color Filtering**: Converts the camera feed to HSV and applies color masks for red and green.
- **Contour Detection**: Identifies contours in the filtered image to locate the cubes.
- **Distance Estimation**: Calculates distance based on the area of the cube's contour using:
  \[
  \text{Distance} = \frac{\text{Focal Length} \times \text{Known Size}}{\sqrt{\text{Contour Area}}}
  \]

### **Motor Control**
- **Forward and Backward Movement**: Uses PWM signals to control motor speed and direction.
- **Proportional Feedback**: Adjusts motor speeds to correct lateral deviations for accurate tracking.

### **Decision Logic**
- Stops at **20 cm** for green cubes and **40 cm** for red cubes.
- Prioritizes the closer cube if both are visible.

---

## 🎥 Results

### **Video Demonstration**
[Watch the robot in action!](https://github.com/user-attachments/assets/cube-tracking-demo)

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

💡 **Pro Tip**: Fine-tune the HSV range for your environment's lighting conditions and adjust motor speed constants for smoother navigation.