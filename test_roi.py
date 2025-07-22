"""
Test ROI Configuration and Violation Logic
This script tests the ROI configuration and violation detection logic without Kafka.
"""

import cv2
import json
import numpy as np
from ultralytics import YOLO
import os

def load_rois():
    """Load ROI configuration"""
    roi_path = "data/rois/rois.json"
    with open(roi_path, 'r') as f:
        return json.load(f)

def is_in_roi(bbox, rois):
    """Check if a bbox is inside any ROI"""
    x1, y1, x2, y2 = bbox
    for idx, roi in enumerate(rois):
        rx1, ry1, rx2, ry2 = roi['x1'], roi['y1'], roi['x2'], roi['y2']
        # Check if bbox center is inside ROI
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        if rx1 <= cx <= rx2 and ry1 <= cy <= ry2:
            return idx
    return None

def test_roi_and_violations():
    print("Testing ROI Configuration and Violation Logic...")
    
    # Load ROIs
    rois = load_rois()
    print(f"Loaded {len(rois)} ROIs:")
    for i, roi in enumerate(rois):
        print(f"   ROI {i}: ({roi['x1']}, {roi['y1']}) to ({roi['x2']}, {roi['y2']})")
    
    # Load model
    model_path = "model/yolo12m-v2.pt"
    model = YOLO(model_path)
    
    # Test with video
    video_path = "data/videos/Sah b3dha ghalt.mp4"
    cap = cv2.VideoCapture(video_path)
    
    frame_count = 0
    total_violations = 0
    
    print(f"Testing violation detection with video: {video_path}")
    
    while cap.isOpened() and frame_count < 50:  # Test first 50 frames
        ret, frame = cap.read()
        if not ret:
            break
        
        # Run detection
        results = model(frame)
        detections = []
        
        # Parse results
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    xyxy = box.xyxy[0].cpu().numpy()
                    conf = box.conf[0].cpu().numpy()
                    cls = int(box.cls[0].cpu().numpy())
                    label = result.names[cls]
                    bbox = [int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])]
                    detections.append({"label": label, "bbox": bbox, "score": float(conf)})
        
        # Check for violations
        frame_violations = []
        for idx, roi in enumerate(rois):
            hand_in_roi = False
            scooper_in_roi = False
            
            for det in detections:
                if is_in_roi(det["bbox"], [roi]) is not None:
                    if det["label"].lower() == "hand":
                        hand_in_roi = True
                    if det["label"].lower() == "scooper":
                        scooper_in_roi = True
            
            if hand_in_roi and not scooper_in_roi:
                frame_violations.append({"roi_id": idx, "type": "no_scooper"})
                total_violations += 1
        
        if frame_violations:
            print(f"   Frame {frame_count}: {len(frame_violations)} violations detected")
        
        frame_count += 1
    
    cap.release()
    
    print(f"ROI and violation test completed:")
    print(f"   - Processed {frame_count} frames")
    print(f"   - Total violations detected: {total_violations}")
    print(f"   - Expected violations for this video: 1")
    
    return total_violations > 0

if __name__ == "__main__":
    test_roi_and_violations() 