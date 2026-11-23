# 🖥️ Desk Posture and Eye Strain Monitoring System

## 📌 Project Overview

The **Desk Posture and Eye Strain Monitoring System** is a Python-based desktop application designed to help computer users maintain proper sitting posture and develop healthy screen-working habits.

The system uses a webcam and computer vision technology to monitor the user's face, posture, and eye activity in real time. It helps identify possible poor sitting posture and signs of eye strain and provides alerts or reminders to encourage healthier computer usage.

The main aim of this project is to reduce discomfort caused by long hours of computer usage and promote better posture and eye-care awareness among students, employees, and regular computer users.

---

## 🎯 Objectives

- To monitor sitting posture using a webcam.
- To identify incorrect sitting posture.
- To monitor eye activity in real time.
- To provide alerts when posture needs correction.
- To encourage regular eye-care breaks.
- To improve awareness of healthy computer usage.
- To develop a simple and user-friendly monitoring application.

---

## ✨ Features

### 1. Real-Time Webcam Monitoring
- Uses the computer's webcam to capture live video.
- Displays the user's face and posture.
- Processes video frames continuously.

### 2. Face Detection
- Detects the user's face using computer vision.
- Identifies important facial landmarks.
- Helps monitor the user's position in front of the screen.

### 3. Posture Monitoring
- Monitors the user's sitting position.
- Identifies possible incorrect posture.
- Displays posture-related status messages.
- Encourages users to sit properly.

### 4. Eye Activity Monitoring
- Uses facial landmarks to observe eye activity.
- Helps identify possible signs of eye strain.
- Supports awareness of blinking and screen breaks.

### 5. Alert and Notification System
- Displays messages when posture correction is needed.
- Provides reminders to take breaks.
- Helps users maintain healthy working habits.

### 6. User-Friendly Interface
- Developed with a simple graphical interface.
- Easy-to-understand buttons and status messages.
- Provides a live webcam monitoring window.

---

## 🛠️ Technologies Used

### Frontend
- **Python Tkinter** – Used to develop the graphical user interface.
- **Pillow (PIL)** – Used for image processing and displaying webcam frames.

### Backend
- **Python** – Main programming language.
- **OpenCV** – Used for webcam access and image processing.
- **MediaPipe** – Used for face detection and facial landmark tracking.

### Development Tools
- Visual Studio Code (VS Code)
- Python
- Windows Operating System
- Webcam

---

## ⚙️ System Requirements

### Hardware Requirements
- Computer or Laptop
- Webcam
- Minimum 4 GB RAM
- Processor capable of running Python applications

### Software Requirements
- Windows 10 or Windows 11
- Python 3.12
- Visual Studio Code
- OpenCV
- MediaPipe
- Pillow

---

## 📂 Project Structure

```text
Desk_Posture_Eye_Strain_Monitor/
│
├── main.py
│
├── requirements.txt
│
├── README.md
│
├── assets/
│
└── screenshots/
```

*Note: Update the file structure above if your actual project contains additional Python files or folders.*

---

## 📥 Installation Guide

### Step 1: Clone the Repository

Open your terminal and run:

```bash
git clone https://github.com/USERNAME/REPOSITORY-NAME.git
```

Replace USERNAME and REPOSITORY-NAME with your GitHub details.

### Step 2: Open the Project Folder

```bash
cd REPOSITORY-NAME
```

### Step 3: Create a Virtual Environment

```bash
python -m venv .venv
```

### Step 4: Activate Virtual Environment

For Windows:

```bash
.venv\Scripts\activate
```

### Step 5: Install Required Libraries

```bash
pip install -r requirements.txt
```

If you do not have a requirements.txt file, install the libraries using:

```bash
pip install opencv-python mediapipe pillow
```

### Step 6: Run the Application

```bash
python main.py
```

---

## ▶️ How to Use the Application

1. Open the project in Visual Studio Code.
2. Install the required Python libraries.
3. Connect or enable your webcam.
4. Run the main Python file.
5. Start the webcam monitoring.
6. Allow the application to process the live video.
7. Observe posture and eye activity status messages.
8. Follow the reminders to maintain healthy computer usage.

---

## 🔍 Working Principle

The system works using the following steps:

1. **Video Capture:** The webcam captures live video.
2. **Image Processing:** OpenCV processes the captured video frames.
3. **Face Detection:** MediaPipe identifies the face and facial landmarks.
4. **Posture Analysis:** The application uses detected landmarks to assess posture.
5. **Eye Activity Analysis:** Facial landmarks are used to monitor eye activity.
6. **Feedback:** The application displays relevant status messages and reminders.

---

## 🌟 Advantages

- Easy to use.
- Real-time webcam monitoring.
- Helps improve posture awareness.
- Encourages regular screen breaks.
- Uses commonly available computer vision technologies.
- Useful for students and office workers.

---

## ⚠️ Limitations

- Requires a working webcam.
- Performance may depend on lighting conditions.
- Face detection can be affected by camera positioning.
- Results may vary depending on the user's movement.
- Eye strain indicators are estimates and are not medical diagnoses.

---

## 🔮 Future Enhancements

- Add user login and registration.
- Add daily posture monitoring reports.
- Introduce advanced eye-blink analysis.
- Add customizable break reminders.
- Store monitoring statistics in a database.
- Develop a mobile application.
- Add graphical reports and performance analytics.

---

## 🎓 Applications

- Educational institutions
- Computer laboratories
- Offices and workplaces
- Students studying for long hours
- People working regularly on computers

---

## 📌 Conclusion

The Desk Posture and Eye Strain Monitoring System is designed to encourage healthy computer usage through real-time webcam monitoring and computer vision technology.

By combining Python, OpenCV, MediaPipe, and Tkinter, this project provides a simple desktop application that helps users become more aware of their sitting posture and eye activity.

This project demonstrates how computer vision can be applied to everyday activities to support better working habits and improve user awareness.

---

## 👨‍💻 Project Information

**Project Name:** Desk Posture and Eye Strain Monitoring System

**Domain:** Python Application Development / Computer Vision

**Programming Language:** Python

**Frontend:** Tkinter

**Backend:** OpenCV and MediaPipe

**IDE:** Visual Studio Code

**Platform:** Windows

---

## 📜 Disclaimer

This application is developed for educational and awareness purposes only. It does not provide medical diagnosis or replace professional medical advice.

---

⭐ If you find this project useful, consider giving this repository a star!
