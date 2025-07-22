"""
Debug YOLO Detections
This script helps diagnose the YOLO class confusion issue.
"""

import cv2
import numpy as np
from ultralytics import YOLO
import os

def debug_detections(video_path, num_frames=5):
    """Debug YOLO detections on video frames"""
    print(f"Debugging detections for: {os.path.basename(video_path)}")
    print("=" * 60)
    
    # Load model
    model = YOLO("model/yolo12m-v2.pt")
    print(f"Model classes: {model.names}")
    print(f"Expected mapping: 0=hand, 1=person, 2=pizza, 3=scooper")
    print()
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Could not open video: {video_path}")
        return
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_indices = [int(total_frames * i / num_frames) for i in range(num_frames)]
    
    for i, frame_idx in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            continue
        
        print(f"Frame {i+1} (frame {frame_idx}):")
        print("-" * 40)
        
        # Run detection
        results = model(frame, verbose=False)
        
        detections_by_class = {0: [], 1: [], 2: [], 3: []}  # hand, person, pizza, scooper
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    confidence = float(box.conf[0].cpu().numpy())
                    
                    detections_by_class[class_id].append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': confidence
                    })
        
        # Print detections by class
        for class_id in [0, 1, 2, 3]:
            class_name = model.names[class_id]
            detections = detections_by_class[class_id]
            if detections:
                print(f"  {class_name} (class {class_id}): {len(detections)} detections")
                for j, det in enumerate(detections):
                    bbox = det['bbox']
                    conf = det['confidence']
                    print(f"    {j+1}. Bbox: {bbox}, Confidence: {conf:.3f}")
            else:
                print(f"  {class_name} (class {class_id}): 0 detections")
        
        print()
    
    cap.release()

def main():
    print("YOLO Detection Debug Tool")
    print("=" * 50)
    print("This tool helps diagnose YOLO class confusion issues.")
    print("=" * 50)
    
    videos = [
        "data/videos/Sah b3dha ghalt.mp4",
        "data/videos/Sah w b3dha ghalt (2).mp4", 
        "data/videos/Sah w b3dha ghalt (3).mp4"
    ]
    
    for video_path in videos:
        if os.path.exists(video_path):
            debug_detections(video_path)
        else:
            print(f"Video not found: {video_path}")
    
    print("=" * 50)
    print("Debug complete!")
    print("Check if the detections match what you see in the videos.")

if __name__ == "__main__":
    main() 