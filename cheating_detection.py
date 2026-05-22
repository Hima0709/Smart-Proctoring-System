import cv2
import torch
import time
import os

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

# Allowed objects (only person is allowed)
ALLOWED_OBJECTS = ["person"]

# Ensure violations directory exists
os.makedirs("violations", exist_ok=True)

# File to store cheating status
CHEATING_STATUS_FILE = "cheating_status.txt"

def detect_cheating():
    cap = cv2.VideoCapture(0)  # Open webcam
    cheat_count = 0  # Counter for cheating detections

    while cheat_count < 3:
        ret, frame = cap.read()
        if not ret:
            break

        # Run YOLO detection
        results = model(frame)
        detections = results.pandas().xyxy[0]  # Get detected objects

        # Check for unauthorized objects
        cheating_detected = any(obj not in ALLOWED_OBJECTS for obj in detections["name"])

        if cheating_detected:
            cheat_count += 1
            img_path = f"violations/cheating_{int(time.time())}.jpg"
            cv2.imwrite(img_path, frame)  # Save cheating image
            print(f"⚠️ Cheating detected! Image saved: {img_path}")

            # Write cheating status to file
            with open(CHEATING_STATUS_FILE, "w") as f:
                f.write("CHEATING")

        time.sleep(2)  # Check every second

    cap.release()
    
    # If 3 violations, log cheating permanently
    if cheat_count >= 3:
        with open(CHEATING_STATUS_FILE, "w") as f:
            f.write("EXAM_TERMINATED")
        print("🚨 Exam Terminated due to excessive cheating detections! 🚨")

if __name__ == "__main__":
    detect_cheating()
