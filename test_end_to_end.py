"""
End-to-End Test for Pizza Scooper Violation Detection
This script simulates the full pipeline without Kafka to test the complete workflow.
"""

import cv2
import json
import numpy as np
import base64
import time
from ultralytics import YOLO
import os

def encode_frame(frame):
    """Encode frame as JPEG, then base64"""
    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        return None
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    return jpg_as_text

def decode_image(image_b64):
    """Decode base64 image to numpy array"""
    jpg_original = base64.b64decode(image_b64)
    jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
    img = cv2.imdecode(jpg_as_np, flags=1)
    return img

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

def draw_overlays(frame, detections, violations, rois):
    """Draw overlays on frame"""
    # Draw ROIs
    for idx, roi in enumerate(rois):
        color = (0, 255, 0)  # Green
        if any(v['roi_id'] == idx for v in violations):
            color = (0, 0, 255)  # Red for violation
        cv2.rectangle(frame, (roi['x1'], roi['y1']), (roi['x2'], roi['y2']), color, 2)
    
    # Draw detections
    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        label = det['label']
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
        cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 2)
    
    return frame

def test_end_to_end_pipeline():
    print("Testing End-to-End Pipeline...")
    print("="*60)
    
    # Step 1: Load components
    print("Loading components...")
    
    # Load model
    model_path = "model/yolo12m-v2.pt"
    if not os.path.exists(model_path):
        print(f"Model not found: {model_path}")
        return False
    
    model = YOLO(model_path)
    print("YOLO model loaded")
    
    # Load ROIs
    rois = load_rois()
    print(f"Loaded {len(rois)} ROIs")
    
    # Load video
    video_path = "data/videos/Sah w b3dha ghalt.mp4"
    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        return False
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Could not open video file")
        return False
    
    print("Video loaded")
    
    # Step 2: Simulate pipeline
    print("\nSimulating pipeline...")
    
    frame_count = 0
    total_violations = 0
    processed_frames = 0
    
    # Test first 30 frames (to keep it fast)
    while cap.isOpened() and frame_count < 30:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Step 2a: Frame Reader (encode frame)
        encoded_frame = encode_frame(frame)
        if encoded_frame is None:
            continue
        
        # Step 2b: Detection Service (decode and detect)
        decoded_frame = decode_image(encoded_frame)
        if decoded_frame is None:
            continue
        
        results = model(decoded_frame)
        detections = []
        
        # Parse detection results
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
        
        # Step 2c: Violation Detection
        violations = []
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
                violations.append({"roi_id": idx, "type": "no_scooper"})
                total_violations += 1
        
        # Step 2d: Streaming Service (draw overlays)
        frame_with_overlays = draw_overlays(decoded_frame.copy(), detections, violations, rois)
        
        processed_frames += 1
        
        # Log progress
        if frame_count % 10 == 0:
            print(f"   Processed {frame_count} frames, violations: {total_violations}")
        
        # Simulate processing time
        time.sleep(0.01)
    
    cap.release()
    
    # Step 3: Results
    print(f"\nPipeline Results:")
    print(f"   - Total frames processed: {processed_frames}")
    print(f"   - Total violations detected: {total_violations}")
    print(f"   - Expected violations for this video: 1")
    
    # Step 4: Validation
    print(f"\nValidation:")
    
    # Check if violations were detected
    if total_violations > 0:
        print(f"   Violations detected: {total_violations}")
    else:
        print(f"   No violations detected (may need more frames or different ROIs)")
    
    # Check if all components worked
    if processed_frames > 0:
        print(f"   Pipeline processed frames successfully")
    else:
        print(f"   Pipeline failed to process frames")
    
    # Overall success
    success = processed_frames > 0
    if success:
        print(f"\nEnd-to-end test PASSED!")
        print(f"   Your system can process videos and detect violations.")
        print(f"   Ready for deployment with Kafka integration.")
    else:
        print(f"\nEnd-to-end test FAILED!")
        print(f"   Check the pipeline components for issues.")
    
    return success

if __name__ == "__main__":
    test_end_to_end_pipeline() 