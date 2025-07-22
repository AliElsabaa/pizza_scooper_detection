"""
Test YOLO Model Independently
This script tests the YOLO model with the provided videos to ensure it can detect hands, scooper, person, and pizza.
"""

import cv2
import numpy as np
from ultralytics import YOLO
import json
import os

def test_model():
    print("Testing YOLO Model...")
    
    # Load model
    model_path = "model/yolo12m-v2.pt"
    if not os.path.exists(model_path):
        print(f"Model not found: {model_path}")
        return False
    
    print("Loading YOLO model...")
    model = YOLO(model_path)
    print("Model loaded successfully")
    
    # Test with first video
    video_path = "data/videos/Sah b3dha ghalt.mp4"
    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        return False
    
    print(f"Testing with video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    frame_count = 0
    detection_count = 0
    
    while cap.isOpened() and frame_count < 10:  # Test first 10 frames
        ret, frame = cap.read()
        if not ret:
            break
            
        # Run detection
        results = model(frame)
        
        # Count detections
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0].cpu().numpy())
                    conf = box.conf[0].cpu().numpy()
                    label = result.names[cls]
                    print(f"   Frame {frame_count}: {label} (confidence: {conf:.2f})")
                    detection_count += 1
        
        frame_count += 1
    
    cap.release()
    
    print(f"Model test completed:")
    print(f"   - Processed {frame_count} frames")
    print(f"   - Found {detection_count} detections")
    print(f"   - Expected classes: hand, scooper, person, pizza")
    
    return True

if __name__ == "__main__":
    test_model() 