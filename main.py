import cv2
from ultralytics import YOLO
import numpy as np
import pygame
import mediapipe as mp
import cvzone
import os
from utils.tracker import Tracker
from utils.log_manager import start_new_session, update_detection, end_session, update_location
import geocoder 

pygame.init()
pygame.mixer.music.load("utils/alarm.wav")

accident_model = YOLO("models/accident_yolo.pt")
fire_smoke_model = YOLO("models/fire_smoke_yolo.pt")
blood_model = YOLO("models/blood_classifier.pt")
human_model = YOLO("models/yolov8n.pt")

with open("coco.txt", "r") as f:
    classes = f.read().split("\n")

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

fall_threshold = 1
tracker = Tracker()

cap = cv2.VideoCapture("data/test_videof.mp4")
if not cap.isOpened():
    print("Error: Video not found or can't be opened.")
    exit()

# Start new log session
session_id = start_new_session()

detected_once = {}

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (1020, 700))
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    ### BLOOD
    blood_results = blood_model(frame)
    blood_label = blood_results[0].probs.top1
    blood_conf = blood_results[0].probs.top1conf
    if blood_label == 0:
        cv2.putText(frame, f"Blood Detected ({blood_conf:.2f})", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        detected_once["blood"] = detected_once.get("blood", 0) + 1

    ### ACCIDENT
    accident_results = accident_model(frame)[0]
    frame = accident_results.plot()
    for box in accident_results.boxes:
        detected_once["accident"] = detected_once.get("accident", 0) + 1

    ### FIRE/SMOKE
    fire_results = fire_smoke_model(frame)[0]
    frame = fire_results.plot()
    for box in fire_results.boxes:
        cls = int(box.cls[0])
        if cls == 0:
            detected_once["fire"] = detected_once.get("fire", 0) + 1
        elif cls == 2:
            detected_once["smoke"] = detected_once.get("smoke", 0) + 1

    ### HUMAN + FALL
    result_pose = pose.process(rgb_frame)
    if result_pose.pose_landmarks:
        mp_drawing.draw_landmarks(frame, result_pose.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                  mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2),
                                  mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2))

    person_results = human_model(frame)[0]
    lis = []
    for box in person_results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        if int(box.cls[0]) < len(classes):
            name = classes[int(box.cls[0])]
            if "person" in name and box.conf[0] > 0.5:
                lis.append([x1, y1, x2, y2])

    bbox_id = tracker.update(lis)
    for bb in bbox_id:
        x1, y1, x2, y2, pid = bb
        width, height = x2 - x1, y2 - y1
        fall_ratio = width / height

        cvzone.cornerRect(frame, (x1, y1, width, height), l=20, t=10)

        if fall_ratio > fall_threshold:
            detected_once["lying_person"] = detected_once.get("lying_person", 0) + 1
            cvzone.putTextRect(frame, "Fall Detected!", (x1, y1 - 40), 2, 3, colorR=(0, 0, 255))
            cvzone.cornerRect(frame, (x1, y1, width, height), l=20, t=10, colorR=(255, 0, 0))
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play()

    cv2.imshow("Multi Detection System", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Final sticky logic: if detected at least once, mark as Yes
for label, count in detected_once.items():
    if count > 0:
        update_detection(session_id, label)

# End session and calculate final severity
end_session(session_id)

g = geocoder.ip('me')
lat, lon = g.latlng if g.ok else (None, None)
location = g.city or "Unknown"

import json
from datetime import datetime
def update_accident_db(labels, severity):
    accident_entry = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "location": location,  # We'll update this later
        "severity": severity,
        "labels": labels,
        "ambulance_enroute": False,
        "lat": lat,
        "lon": lon,
        "severity": severity,
    }
    with open("logs/accident_db.json", "w") as f:
        json.dump(accident_entry, f, indent=2)

update_location(session_id, lat, lon, location)
update_accident_db(final_labels, severity_score)



