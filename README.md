# Study Guardian

**Study Guardian** is a real-time drowsiness and yawn detection tool that helps students stay alert while studying. It uses your webcam and computer vision techniques to detect when you're closing your eyes for too long or yawning — and plays an alert sound to snap you back into focus!

---

## 🔍 Features

- 👁️ Detects prolonged eye closure using facial landmarks.
- 😮 Detects yawning based on mouth openness.
- 🔊 Plays an alert sound when you're dozing off.
- 💻 Runs in real-time using your webcam.

---

## How It Works

- Uses **MediaPipe FaceMesh** to track key facial points.
- Calculates **Eye Aspect Ratio (EAR)** and **Mouth Aspect Ratio (MAR)**.
- Plays a custom alert sound when sleepiness is detected.

---

## Requirements

Make sure you have **Python 3.7+** installed.

Install the dependencies:

```bash
pip install opencv-python mediapipe pygame
