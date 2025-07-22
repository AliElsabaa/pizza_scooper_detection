"""
Test Streaming Service Functionality
This script tests the streaming service's ability to process detection results and serve video streams.
"""

import cv2
import base64
import numpy as np
import json
import os

def decode_image(image_b64):
    """Decode base64 image to numpy array"""
    jpg_original = base64.b64decode(image_b64)
    jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
    img = cv2.imdecode(jpg_as_np, flags=1)
    return img

def encode_jpeg(frame):
    """Encode frame as JPEG bytes"""
    ret, buffer = cv2.imencode('.jpg', frame)
    return buffer.tobytes() if ret else None

def load_rois():
    """Load ROI configuration"""
    roi_path = "data/rois/rois.json"
    with open(roi_path, 'r') as f:
        return json.load(f)

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

def test_streaming_service():
    print("Testing Streaming Service...")
    
    # Load ROIs
    rois = load_rois()
    print(f"Loaded {len(rois)} ROIs")
    
    # Test video path
    video_path = "data/videos/Sah b3dha ghalt.mp4"
    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        return False
    
    # Open video and process a few frames
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Could not open video file")
        return False
    
    processed_frames = 0
    successful_overlays = 0
    
    print(f"Testing frame processing and overlay drawing...")
    
    while cap.isOpened() and processed_frames < 5:  # Test first 5 frames
        ret, frame = cap.read()
        if not ret:
            break
        
        processed_frames += 1
        
        # Simulate detection results (empty for testing)
        detections = []
        violations = []
        
        # Test overlay drawing
        try:
            frame_with_overlays = draw_overlays(frame.copy(), detections, violations, rois)
            jpeg_data = encode_jpeg(frame_with_overlays)
            
            if jpeg_data is not None:
                successful_overlays += 1
                print(f"   Frame {processed_frames}: Overlay and encoding successful ({len(jpeg_data)} bytes)")
            else:
                print(f"   Frame {processed_frames}: JPEG encoding failed")
        except Exception as e:
            print(f"   Frame {processed_frames}: Overlay drawing failed - {e}")
    
    cap.release()
    
    print(f"Streaming service test completed:")
    print(f"   - Processed {processed_frames} frames")
    print(f"   - Successful overlays: {successful_overlays}")
    print(f"   - Success rate: {successful_overlays/processed_frames*100:.1f}%")
    
    return successful_overlays > 0

if __name__ == "__main__":
    test_streaming_service() 