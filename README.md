# Study Guardian

A Flask-based application that helps you stay focused during study sessions using the Pomodoro Technique and computer vision-based drowsiness detection.

## Features

- 🎥 Real-time drowsiness detection using webcam
- ⏲️ Pomodoro timer (25 minutes work, 5 minutes break)
- 📝 Task management system
- 🔔 Audio alerts for drowsiness detection
- 📊 Session tracking

## Prerequisites

- Python 3.8 or higher
- Webcam
- Modern web browser
- Audio output device

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/study-guardian.git
cd study-guardian
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Make sure you have the `alert.wav` file in the project directory for audio alerts.

2. Start the Flask application:
```bash
python app.py
```

3. Open your web browser and navigate to:
```
http://localhost:5000
```

4. Click "Start Studying" to begin your Pomodoro session:
   - The webcam will activate and monitor for signs of drowsiness
   - The timer will start counting down from 25 minutes
   - Add tasks using the task management panel
   - Audio alerts will play if drowsiness is detected

5. After 25 minutes, you'll get a 5-minute break
   - The process repeats until you click "Stop"

## How it Works

- The application uses MediaPipe Face Mesh to detect facial landmarks
- Eye Aspect Ratio (EAR) is calculated to detect drowsiness
- Mouth Aspect Ratio (MAR) is used to detect yawning
- The Pomodoro timer helps maintain focus with structured work/break periods
- Tasks are managed through a simple interface and stored on the server

## Contributing

Feel free to submit issues and enhancement requests! 