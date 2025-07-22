"""
Visual ROI Creation Tool
This tool helps create proper ROIs for each video by showing frames and allowing interactive definition.
"""

import cv2
import json
import os
import numpy as np
from datetime import datetime

def draw_roi_on_frame(frame, rois, current_roi=None):
    """Draw ROIs on frame"""
    frame_copy = frame.copy()
    
    # Draw existing ROIs
    for i, roi in enumerate(rois):
        color = (0, 255, 0) if i != current_roi else (0, 0, 255)
        cv2.rectangle(frame_copy, (roi['x1'], roi['y1']), (roi['x2'], roi['y2']), color, 2)
        cv2.putText(frame_copy, f"ROI {i+1}", (roi['x1'], roi['y1']-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    return frame_copy

def create_roi_interactive(video_path, output_path):
    """Create ROIs interactively for a video"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Could not open video: {video_path}")
        return False
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Video: {os.path.basename(video_path)}")
    print(f"Total frames: {total_frames}, FPS: {fps:.2f}")
    print("Controls:")
    print("- Click and drag to create ROI")
    print("- Press 'n' for next frame")
    print("- Press 'p' for previous frame")
    print("- Press 's' to save ROIs")
    print("- Press 'q' to quit")
    
    rois = []
    current_frame = 0
    drawing = False
    start_point = None
    current_roi = None
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal drawing, start_point, current_roi
        
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            start_point = (x, y)
            current_roi = len(rois)
            rois.append({'x1': x, 'y1': y, 'x2': x, 'y2': y})
        
        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            rois[current_roi]['x2'] = x
            rois[current_roi]['y2'] = y
        
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            # Ensure x1,y1 is top-left and x2,y2 is bottom-right
            x1, y1 = min(rois[current_roi]['x1'], rois[current_roi]['x2']), min(rois[current_roi]['y1'], rois[current_roi]['y2'])
            x2, y2 = max(rois[current_roi]['x1'], rois[current_roi]['x2']), max(rois[current_roi]['y1'], rois[current_roi]['y2'])
            rois[current_roi]['x1'], rois[current_roi]['y1'] = x1, y1
            rois[current_roi]['x2'], rois[current_roi]['y2'] = x2, y2
    
    window_name = f"ROI Creation - {os.path.basename(video_path)}"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback)
    
    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        ret, frame = cap.read()
        if not ret:
            break
        
        # Draw ROIs on frame
        display_frame = draw_roi_on_frame(frame, rois, current_roi)
        
        # Add frame info
        cv2.putText(display_frame, f"Frame: {current_frame}/{total_frames}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display_frame, f"ROIs: {len(rois)}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow(window_name, display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('n'):
            current_frame = min(current_frame + 30, total_frames - 1)  # Skip 1 second
        elif key == ord('p'):
            current_frame = max(current_frame - 30, 0)  # Go back 1 second
        elif key == ord('s'):
            # Save ROIs
            roi_data = {
                "video_name": os.path.splitext(os.path.basename(video_path))[0],
                "created_at": datetime.now().isoformat(),
                "description": f"ROIs for {os.path.basename(video_path)} - Define protein container areas where scooper is required",
                "rois": rois
            }
            
            with open(output_path, 'w') as f:
                json.dump(roi_data, f, indent=2)
            
            print(f"ROIs saved to: {output_path}")
            print(f"Created {len(rois)} ROIs")
            break
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    return True

def main():
    print("Visual ROI Creation Tool for Pizza Scooper Violation Detection")
    print("=" * 70)
    
    videos = [
        "data/videos/Sah b3dha ghalt.mp4",
        "data/videos/Sah w b3dha ghalt (2).mp4", 
        "data/videos/Sah w b3dha ghalt (3).mp4"
    ]
    
    for video_path in videos:
        if os.path.exists(video_path):
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = f"data/rois/{video_name}_rois.json"
            
            print(f"\nCreating ROIs for: {video_name}")
            print("-" * 50)
            
            if create_roi_interactive(video_path, output_path):
                print(f"✅ ROIs created for {video_name}")
            else:
                print(f"❌ Failed to create ROIs for {video_name}")
        else:
            print(f"Video not found: {video_path}")
    
    print("\n" + "=" * 70)
    print("ROI Creation Complete!")
    print("You can now run the video testing with proper ROIs.")

if __name__ == "__main__":
    main() 