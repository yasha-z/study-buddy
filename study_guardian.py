import cv2
import mediapipe as mp
import math
import threading
import pygame
import time

# Initialize pygame mixer and load the alert sound once
pygame.mixer.init()
alert_sound = pygame.mixer.Sound("alert.wav")  # Ensure this file exists in the same folder

# Function to play alert sound in the background
def play_alert():
    if not pygame.mixer.get_busy():  # Avoid overlapping alerts
        alert_sound.play()

# Setup MediaPipe FaceMesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)

# Eye and mouth landmarks for detection
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
MOUTH = [13, 14]

# Function to calculate Euclidean distance
def distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

# Start the webcam
cap = cv2.VideoCapture(0)
sleep_counter = 0
eye_closed_time = 0  # Track time for closed eyes

print("Study Guardian is running. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        face = results.multi_face_landmarks[0]
        landmarks = face.landmark

        # Get coordinates for eyes and mouth
        def get_coords(points):
            return [(int(landmarks[p].x * w), int(landmarks[p].y * h)) for p in points]

        left_eye = get_coords(LEFT_EYE)
        right_eye = get_coords(RIGHT_EYE)
        mouth = get_coords(MOUTH)

        # Calculate Eye Aspect Ratio (EAR)
        def get_ear(eye):
            v1 = distance(eye[1], eye[5])
            v2 = distance(eye[2], eye[4])
            h1 = distance(eye[0], eye[3])
            return (v1 + v2) / (2.0 * h1)

        left_ear = get_ear(left_eye)
        right_ear = get_ear(right_eye)
        ear = (left_ear + right_ear) / 2.0

        # Detect yawning based on mouth aspect ratio
        mouth_open = distance(mouth[0], mouth[1])
        mar = mouth_open / w

        # Sleeping detection: Eye closure for more than 2 seconds
        if ear < 0.25:
            eye_closed_time += 1
            if eye_closed_time > 60:  # Assuming ~30 FPS
                cv2.putText(frame, "EYES CLOSED! WAKE UP!", (30, 100), cv2.FONT_HERSHEY_SIMPLEX,
                            1.2, (0, 0, 255), 3)
                threading.Thread(target=play_alert).start()
        else:
            eye_closed_time = 0  # Reset if eyes are open

        # Yawning detection
        if mar > 0.03:
            cv2.putText(frame, "YAWNING... Stay awake!", (30, 150), cv2.FONT_HERSHEY_SIMPLEX,
                        0.9, (255, 0, 0), 2)

    # Display the frame
    cv2.imshow("Study Guardian", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
