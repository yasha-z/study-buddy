from flask import Flask, render_template, Response, jsonify, request
import cv2
import mediapipe as mp
import math
import threading
import time
import pygame
from datetime import datetime
import numpy as np
import random

app = Flask(__name__)

# Initialize MediaPipe FaceMesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)

# Initialize sound
pygame.mixer.init()
alert_sound = pygame.mixer.Sound("alert.wav")

# Constants
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
MOUTH = [13, 14]

# Task types and their specific motivational quotes
TASK_TYPES = {
    "reading": "Reading",
    "writing": "Writing",
    "problem_solving": "Problem Solving",
    "memorization": "Memorization",
    "research": "Research"
}

TASK_SPECIFIC_QUOTES = {
    "reading": [
        "Take it one page at a time! 📚",
        "Every paragraph brings new knowledge! 🎯",
        "Reading is to the mind what exercise is to the body! 💪"
    ],
    "writing": [
        "Let your ideas flow freely! ✍️",
        "Your words have power! 🌟",
        "Write first, edit later! 📝"
    ],
    "problem_solving": [
        "Break it down, solve it up! 🧩",
        "Every problem is a new opportunity! 🎯",
        "Think outside the box! 💡"
    ],
    "memorization": [
        "Repetition is the mother of learning! 🔄",
        "Your brain is a sponge! 🧠",
        "Connect the dots! 🎯"
    ],
    "research": [
        "Explore the unknown! 🔍",
        "Every search leads to discovery! 🌟",
        "Connect the pieces of knowledge! 🧩"
    ]
}

# General motivational quotes
GENERAL_QUOTES = [
    "You've got this! Just a little more focus! 💪",
    "Take a deep breath, stay strong! 🌟",
    "Remember why you started! 🎯",
    "Your future self will thank you! 🚀",
    "Small steps lead to big achievements! 🎓",
    "Stay focused, stay amazing! ✨",
    "You're doing great! Keep pushing! 🌈",
    "Success is built one study session at a time! 📚",
    "Believe in yourself! You can do this! ⭐",
    "Every minute of focus counts! 🎯"
]

# Global variables
tasks = {}  # Format: {task: {"completed": bool, "completed_in_session": int or None, "type": str, "drowsiness_events": list}}
camera = None
is_monitoring = False
eye_closed_time = 0
current_quote = ""
last_quote_time = 0
tiredness_counter = 0
drowsiness_patterns = []  # List to store timestamps of drowsiness events

def distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def get_ear(eye):
    v1 = distance(eye[1], eye[5])
    v2 = distance(eye[2], eye[4])
    h1 = distance(eye[0], eye[3])
    return (v1 + v2) / (2.0 * h1)

def play_alert():
    if not pygame.mixer.get_busy():
        alert_sound.play()

def get_smart_break_suggestion():
    if not drowsiness_patterns:
        return None
        
    # Calculate time since last break
    current_time = time.time()
    time_since_last_break = current_time - drowsiness_patterns[-1]
    
    # If we have multiple drowsiness events in the last 5 minutes
    recent_events = [t for t in drowsiness_patterns if current_time - t <= 300]
    
    if len(recent_events) >= 3:
        return "High drowsiness detected. Consider taking a break now!"
    elif len(recent_events) >= 2:
        return "You're showing signs of tiredness. A break might be helpful soon."
    elif time_since_last_break > 1500:  # 25 minutes
        return "You've been studying for a while. Consider a short break soon."
    
    return None

def get_task_specific_quote(task_type=None):
    current_time = time.time()
    
    if task_type and task_type in TASK_SPECIFIC_QUOTES:
        quotes = TASK_SPECIFIC_QUOTES[task_type]
    else:
        quotes = GENERAL_QUOTES
        
    return random.choice(quotes)

def generate_frames():
    global camera, is_monitoring, eye_closed_time, tiredness_counter, current_quote, last_quote_time, drowsiness_patterns
    
    if camera is None:
        camera = cv2.VideoCapture(0)
    
    while is_monitoring:
        success, frame = camera.read()
        if not success:
            break
        
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            face = results.multi_face_landmarks[0]
            landmarks = face.landmark

            def get_coords(points):
                return [(int(landmarks[p].x * w), int(landmarks[p].y * h)) for p in points]

            left_eye = get_coords(LEFT_EYE)
            right_eye = get_coords(RIGHT_EYE)
            mouth = get_coords(MOUTH)

            left_ear = get_ear(left_eye)
            right_ear = get_ear(right_eye)
            ear = (left_ear + right_ear) / 2.0
            mar = distance(mouth[0], mouth[1]) / w

            current_time = time.time()
            if ear < 0.25:
                eye_closed_time += 1
                tiredness_counter += 1
                if eye_closed_time > 30:
                    cv2.putText(frame, "EYES CLOSED!", (30, 100),
                              cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                    threading.Thread(target=play_alert).start()
                    # Record drowsiness event
                    drowsiness_patterns.append(current_time)
            else:
                eye_closed_time = 0

            if mar > 0.03:
                tiredness_counter += 1
                cv2.putText(frame, "YAWNING...", (30, 150),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                # Record drowsiness event for yawning
                drowsiness_patterns.append(current_time)

            # Update quote if tired or based on task type
            if tiredness_counter > 50 and current_time - last_quote_time > 10:
                # Find current active task type
                active_task_type = None
                for task, data in tasks.items():
                    if not data["completed"]:
                        active_task_type = data.get("type")
                        break
                
                current_quote = get_task_specific_quote(active_task_type)
                last_quote_time = current_time
                tiredness_counter = 0

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_monitoring', methods=['POST'])
def start_monitoring():
    global is_monitoring, eye_closed_time
    is_monitoring = True
    eye_closed_time = 0  # Reset eye closed time when starting new session
    return jsonify({"status": "success"})

@app.route('/stop_monitoring', methods=['POST'])
def stop_monitoring():
    global is_monitoring, camera, eye_closed_time
    is_monitoring = False
    eye_closed_time = 0
    if camera is not None:
        camera.release()
        camera = None
    return jsonify({"status": "success"})

@app.route('/tasks', methods=['GET', 'POST'])
def manage_tasks():
    global tasks
    if request.method == 'POST':
        data = request.get_json()
        if 'task' in data and 'type' in data:
            tasks[data['task']] = {
                "completed": False,
                "completed_in_session": None,
                "type": data['type'],
                "drowsiness_events": []
            }
            return jsonify({"status": "success"})
    return jsonify(tasks)

@app.route('/update_task', methods=['POST'])
def update_task():
    global tasks
    data = request.get_json()
    if 'task' in data and 'completed' in data and 'session' in data:
        task = data['task']
        completed = data['completed']
        session = data['session']
        
        if task in tasks:
            tasks[task]["completed"] = completed
            if completed:
                tasks[task]["completed_in_session"] = session
            else:
                tasks[task]["completed_in_session"] = None
            return jsonify({"status": "success", "task": task, "completed_in_session": tasks[task]["completed_in_session"]})
    return jsonify({"status": "error"})

@app.route('/get_quote')
def get_quote():
    global current_quote
    return jsonify({
        "quote": current_quote,
        "has_quote": bool(current_quote)
    })

@app.route('/get_break_suggestion')
def get_break_suggestion():
    suggestion = get_smart_break_suggestion()
    return jsonify({
        "suggestion": suggestion,
        "has_suggestion": bool(suggestion)
    })

if __name__ == '__main__':
    app.run(debug=True) 