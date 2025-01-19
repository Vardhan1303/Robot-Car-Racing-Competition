# Robot Car Racing Competition

## Overview
The **Robot Car Racing Competition** is a subject as part of the Master's program in Mechatronics and Embedded System at RWU (Ravensburg-Weingarten University of Applied Sciences). This project was guided and supervised by **Mr. Tobias Niederman**. 

The primary objective of this course is to design and program an autonomous robot car capable of solving a series of tasks using computer vision, LiDAR sensors, and embedded systems. 

### Authors
- **Vardhan Mistry**
- **Rajveersinh Suratiya**

---

## Repository Structure
This repository is organized into four main folders, one for each task of the competition. Each folder contains:

1. The Python code implementing the task.
2. A README file explaining the task-specific implementation.
3. Videos and photos demonstrating the robot solving the task.

### Folder Structure
```plaintext
Robot-Car-Racing-Competition/
│
├── Task1_Line_Following/
│   ├── task1_line_following.py
│   ├── README.md
│   ├── videos/
│   └── images/
│
├── Task2_LiDAR_Stop/
│   ├── task2_lidar_stop.py
│   ├── README.md
│   ├── videos/
│   └── images/
│
├── Task3_Color_Cube_Detection/
│   ├── task3_color_cube_detection.py
│   ├── README.md
│   ├── videos/
│   └── images/
│
├── Task4_ArUco_Cube_Detection/
│   ├── task4_aruco_cube_detection.py
│   ├── README.md
│   ├── videos/
│   └── images/
│
├── README.md  (This File)
└── Line.pdf  (Line layout reference)
```

---

## General Description of Tasks

### Task 1: Line Following
The robot uses a camera to follow a line created using sheets of paper (described in `Line.pdf`). The algorithm processes the camera feed, detects the line, and adjusts the robot's movement to stay on track. Thresholds for line detection were fine-tuned for optimal performance in H216.

**Hardware Used**: Raspberry Pi 4, Camera

---

### Task 2: LiDAR-Based Stopping
The robot uses a LiDAR sensor to detect obstacles and stop 20 cm in front of them. This feature works seamlessly while the robot is following the line from Task 1.

**Hardware Used**: Raspberry Pi 4, LiDAR Sensor

---

### Task 3: Color Cube Detection
The robot detects and moves towards green and red cubes, stopping at different distances:
- 20 cm for green cubes
- 40 cm for red cubes

If no cubes are visible, the robot remains stationary. If both cubes are visible, the robot moves toward the closer one.

**Hardware Used**: Raspberry Pi 4, Camera

---

### Task 4: ArUco Marker Cube Detection
The robot detects cubes marked with ArUco markers (6x6 ID 0 and ID 1) and stops at specific distances:
- 20 cm for ID 0
- 40 cm for ID 1

Similar to Task 3, if both markers are visible, the robot approaches the closer one.

**Hardware Used**: Raspberry Pi 4, Camera

---

## Technologies and Tools
- **Programming Language**: Python
- **Libraries**: OpenCV, NumPy, RPi.GPIO
- **Hardware**: Raspberry Pi 4, Camera

---

## How to Run the Code
Each task folder contains a `README.md` file with detailed instructions for running the corresponding code. In general:

1. Clone the repository:
   ```bash
   git clone https://github.com/VArdhan1303/Robot-Car-Racing-Competition.git
   cd Robot-Car-Racing-Competition
   ```

2. Navigate to the desired task folder:
   ```bash
   cd Task1_Line_Following
   ```

3. Run the Python script:
   ```bash
   python3 task1_line_following.py
   ```

4. Follow instructions in the task-specific `README.md` for setup and testing.

---

## Notes
- This algorithm and code will work only on Raspberry Pi 4. If you want to run it on other hardware, you will need to modify the code according to the hardware specifications.
- This project is intended solely for learning and expanding knowledge in the ADAS (Advanced Driver-Assistance Systems) field.
- You are not permitted to copy or publish this work without our explicit permission.

---

## Acknowledgements
We express our gratitude to **Mr. Tobias Niederman** for his guidance and support throughout this project. The course provided invaluable experience in robotics, computer vision, and sensor integration.
