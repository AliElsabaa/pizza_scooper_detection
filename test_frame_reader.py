"""
Test Frame Reader Functionality
This script tests the frame reader's ability to process video frames without Kafka.
"""

import cv2
import base64
import time
import os

def encode_frame(frame):
    """Encode frame as JPEG, then base64"""
    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        return None
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    return jpg_as_text

def test_frame_reader():
    print("Testing Frame Reader...")
    
    # Test video path
    video_path = "data/videos/Sah b3dha ghalt.mp4"
    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        return False
    
    print(f"Testing frame reading from: {video_path}")
    
    # Open video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Could not open video file")
        return False
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Video properties:")
    print(f"   - FPS: {fps}")
    print(f"   - Total frames: {frame_count}")
    print(f"   - Resolution: {width}x{height}")
    
    # Test frame reading and encoding
    processed_frames = 0
    encoded_frames = 0
    
    while cap.isOpened() and processed_frames < 10:  # Test first 10 frames
        ret, frame = cap.read()
        if not ret:
            break
        
        processed_frames += 1
        
        # Test frame encoding
        encoded = encode_frame(frame)
        if encoded is not None:
            encoded_frames += 1
            print(f"   Frame {processed_frames}: Encoded successfully ({len(encoded)} chars)")
        else:
            print(f"   Frame {processed_frames}: Encoding failed")
        
        time.sleep(0.03)  # Simulate ~30 FPS
    
    cap.release()
    
    print(f"Frame reader test completed:")
    print(f"   - Processed {processed_frames} frames")
    print(f"   - Successfully encoded {encoded_frames} frames")
    print(f"   - Success rate: {encoded_frames/processed_frames*100:.1f}%")
    
    return encoded_frames > 0

if __name__ == "__main__":
    test_frame_reader() 