import streamlit as st
import cv2
import mediapipe as mp
import math
import threading
import time
import pygame

# Initialize sound
pygame.mixer.init()
alert_sound = pygame.mixer.Sound("alert.wav")

# MediaPipe FaceMesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
MOUTH = [13, 14]

def distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def play_alert():
    if not pygame.mixer.get_busy():
        alert_sound.play()

def get_ear(eye):
    v1 = distance(eye[1], eye[5])
    v2 = distance(eye[2], eye[4])
    h1 = distance(eye[0], eye[3])
    return (v1 + v2) / (2.0 * h1)

def webcam_monitor(stop_flag, timer_placeholder, video_placeholder, duration_sec):
    cap = cv2.VideoCapture(0)
    start_time = time.time()
    eye_closed_time = 0

    while time.time() - start_time < duration_sec:
        if stop_flag["stop"]:
            break

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        elapsed = int(time.time() - start_time)
        remaining = max(0, duration_sec - elapsed)
        minutes = remaining // 60
        seconds = remaining % 60
        timer_placeholder.markdown(f"⏳ Time Left: **{minutes:02d}:{seconds:02d}**")

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

            if ear < 0.25:
                eye_closed_time += 1
                if eye_closed_time > 60:
                    cv2.putText(frame, "EYES CLOSED!", (30, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                    threading.Thread(target=play_alert).start()
            else:
                eye_closed_time = 0

            if mar > 0.03:
                cv2.putText(frame, "YAWNING...", (30, 150),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

        video_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="RGB")

    cap.release()
    video_placeholder.empty()
    timer_placeholder.markdown("✅ Session complete!")

def run_pomodoro(tasks, stop_flag):
    work_duration = 25 * 60
    break_duration = 5 * 60
    session_count = 0

    timer_placeholder = st.empty()
    video_placeholder = st.empty()
    stop_button = st.button("❌ Stop Studying")

    while not stop_flag["stop"]:
        session_count += 1
        st.markdown(f"### 🔁 Pomodoro Round {session_count}")
        st.success("✅ Starting 25-minute focus session...")
        webcam_monitor(stop_flag, timer_placeholder, video_placeholder, work_duration)

        # Check for stop
        if stop_flag["stop"] or stop_button:
            stop_flag["stop"] = True
            break

        # After work session, check if all tasks completed
        if all(tasks[key] for key in tasks):
            st.balloons()
            st.success(f"🎉 Congratulations! You completed all your tasks in {session_count} Pomodoro session(s)! 🎉")
            stop_flag["stop"] = True
            break

        st.info("☕ Take a 5-minute break! Camera is off.")
        break_start = time.time()
        while time.time() - break_start < break_duration:
            if stop_flag["stop"] or stop_button:
                stop_flag["stop"] = True
                break
            remaining = int(break_duration - (time.time() - break_start))
            minutes, seconds = divmod(remaining, 60)
            timer_placeholder.markdown(f"☕ Break: **{minutes:02d}:{seconds:02d}**")
            time.sleep(1)

        if stop_flag["stop"]:
            break

    timer_placeholder.markdown("🛑 Studying session ended.")

# Streamlit UI
st.set_page_config(page_title="Study Guardian", layout="centered")
st.title("📚 Study Guardian with Task List")
st.markdown("Track your Pomodoro sessions with webcam drowsiness detection and manage your tasks!")

if "tasks" not in st.session_state:
    st.session_state.tasks = {}

if "stop_flag" not in st.session_state:
    st.session_state.stop_flag = {"stop": False}

# Task input
with st.expander("📝 Add Tasks"):
    task_input = st.text_input("Enter a new task:")
    if st.button("➕ Add Task"):
        if task_input.strip() != "":
            st.session_state.tasks[task_input] = False           
            # st.experimental.script_runner.rerun()


# Show task list with checkboxes
if st.session_state.tasks:
    st.markdown("### Your Tasks")
    for task in list(st.session_state.tasks.keys()):
        completed = st.checkbox(task, value=st.session_state.tasks[task])
        st.session_state.tasks[task] = completed

# Start/Stop buttons
if not st.session_state.stop_flag["stop"]:
    if st.button("▶️ Start Studying"):
        st.session_state.stop_flag["stop"] = False
        run_pomodoro(st.session_state.tasks, st.session_state.stop_flag)
else:
    if st.button("🔄 Restart Session"):
        st.session_state.stop_flag["stop"] = False
        st.experimental_rerun()
