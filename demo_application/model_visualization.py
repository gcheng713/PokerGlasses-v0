# Base code provided by Dipankar Medhi article https://dipankarmedh1.medium.com/real-time-object-detection-with-yolo-and-webcam-enhancing-your-computer-vision-skills-861b97c78993
# Note press Q to stop the demo

import math
import sys
from ultralytics import YOLO
import cv2
import numpy as np

# Change to 'tuned' to use it as the default one
DEFAULT_MODEL = "synthetic"
SHOW_CONFIDENCE = False

configuration_dict = {
    "synthetic": {
        "model_path": "../final_models/yolov8m_synthetic.pt",
        "class_names": [
            "10c", "10d", "10h", "10s", "2c", "2d", "2h", "2s",
            "3c", "3d", "3h", "3s", "4c", "4d", "4h", "4s",
            "5c", "5d", "5h", "5s", "6c", "6d", "6h", "6s",
            "7c", "7d", "7h", "7s", "8c", "8d", "8h", "8s",
            "9c", "9d", "9h", "9s", "Ac", "Ad", "Ah", "As",
            "Jc", "Jd", "Jh", "Js", "Kc", "Kd", "Kh", "Ks",
            "Qc", "Qd", "Qh", "Qs",
        ],
    },
    "tuned": {
        "model_path": "../final_models/yolov8m_tuned.pt",
        "class_names": ["10h", "2h", "3h", "4h", "5h", "6h", "7h", "8h", "9h", "Ah", "Jh", "Kh", "Qh"],
    },
}

print("Loading application...")

configuration_model = sys.argv[1] if len(sys.argv) >= 2 else DEFAULT_MODEL

if configuration_model not in configuration_dict.keys():
    print(f"Allowed parameters for model are {configuration_dict.keys()}. Defaulting to {DEFAULT_MODEL}...")
    configuration_model = DEFAULT_MODEL

current_config = configuration_dict.get(configuration_model)

# Load the model and class names
model = YOLO(current_config["model_path"])
classNames = current_config["class_names"]

# Start webcam
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

def draw_card_box(img, detected_cards):
    # Create a black box at the bottom of the screen
    box_height = 60
    box_y = img.shape[0] - box_height
    cv2.rectangle(img, (0, box_y), (img.shape[1], img.shape[0]), (0, 0, 0), -1)
    
    # Draw detected cards in the box
    if detected_cards:
        # Convert set to sorted list for consistent display
        cards_text = sorted(list(detected_cards))
        text = "Detected Cards: " + " ".join(cards_text)
        cv2.putText(img, text, (10, box_y + 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

while True:
    success, img = cap.read()
    if not success:
        break
        
    # Detect objects
    results = model(img, stream=True)
    detected_cards = set()  # Use set to avoid duplicates
    
    # Process detections
    for r in results:
        boxes = r.boxes
        for box in boxes:
            # Get detection confidence
            confidence = math.ceil((box.conf[0] * 100)) / 100
            if confidence < 0.5:  # Filter low confidence detections
                continue
                
            # Get detected class
            cls = int(box.cls[0])
            detected_card = classNames[cls]
            detected_cards.add(detected_card)
            
            # Draw bounding box
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            
            # Draw label
            label = f"{detected_card}"
            if SHOW_CONFIDENCE:
                label += f" {confidence}"
            t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            c2 = x1 + t_size[0], y1 - t_size[1] - 3
            cv2.rectangle(img, (x1, y1), c2, (255, 0, 255), -1, cv2.LINE_AA)
            cv2.putText(img, label, (x1, y1 - 2), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Draw the card box with detected cards
    draw_card_box(img, detected_cards)
    
    # Show image
    cv2.imshow('Poker Card Reader', img)
    
    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
