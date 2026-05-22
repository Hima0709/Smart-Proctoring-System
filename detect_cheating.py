import cv2
import torch
import time
import os

# Automatically download and load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

def detect_objects(frame):
    results = model(frame)
    detections = results.pandas().xyxy[0]
    allowed_objects = ["person"]  # Only person is allowed
    cheating_detected = any(obj not in allowed_objects for obj in detections["name"])
    return cheating_detected

def start_cheating_detection(user_id):
    cap = cv2.VideoCapture(0)
    cheat_count = 0
    
    while cheat_count < 3:
        ret, frame = cap.read()
        if not ret:
            break
        
        if detect_objects(frame):
            cheat_count += 1
            os.makedirs("violations", exist_ok=True)
            img_path = f"violations/user_{user_id}_{time.time()}.jpg"
            cv2.imwrite(img_path, frame)
            print(f"Cheating detected! Image saved: {img_path}")
            
        time.sleep(1)  # Check every second
    
    cap.release()
    if cheat_count >= 3:
        print("Exam terminated due to excessive cheating detections.")
        return False  # Exam should be terminated
    return True
