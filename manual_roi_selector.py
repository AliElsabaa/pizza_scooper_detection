"""
Manual ROI Selector for Pizza Scooper Violation Detection
This script allows manual ROI selection for each video with clear instructions.
"""

import cv2
import json
import os
import numpy as np
from datetime import datetime

def draw_roi_on_frame(frame, rois, current_roi=None, drawing=False, start_point=None, end_point=None):
    """Draw ROIs on frame with current selection"""
    frame_copy = frame.copy()
    
    # Draw existing ROIs
    for i, roi in enumerate(rois):
        color = (0, 255, 0)  # Green for existing ROIs
        cv2.rectangle(frame_copy, (roi['x1'], roi['y1']), (roi['x2'], roi['y2']), color, 2)
        cv2.putText(frame_copy, f"ROI {i+1}", (roi['x1'], roi['y1']-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    # Draw current selection
    if drawing and start_point and end_point:
        cv2.rectangle(frame_copy, start_point, end_point, (0, 0, 255), 2)  # Red for current selection
    
    return frame_copy

def select_rois_for_video(video_path, output_path):
    """Interactive ROI selection for a single video"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Could not open video: {video_path}")
        return False
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"\n{'='*60}")
    print(f"ROI SELECTION FOR: {os.path.basename(video_path)}")
    print(f"{'='*60}")
    print(f"Total frames: {total_frames}, FPS: {fps:.2f}")
    print(f"Duration: {total_frames/fps:.2f} seconds")
    print("\nINSTRUCTIONS:")
    print("1. Navigate to a frame showing the protein containers")
    print("2. Click and drag to create ROIs around protein containers")
    print("3. Press 'n' for next frame, 'p' for previous frame")
    print("4. Press 's' to save ROIs when done")
    print("5. Press 'q' to quit without saving")
    print("6. Press 'r' to reset all ROIs")
    print("\nIMPORTANT: Focus on areas where workers grab ingredients!")
    print(f"{'='*60}")
    
    rois = []
    current_frame = 0
    drawing = False
    start_point = None
    end_point = None
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal drawing, start_point, end_point
        
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            start_point = (x, y)
            end_point = (x, y)
        
        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            end_point = (x, y)
        
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            if start_point and end_point:
                # Ensure x1,y1 is top-left and x2,y2 is bottom-right
                x1, y1 = min(start_point[0], end_point[0]), min(start_point[1], end_point[1])
                x2, y2 = max(start_point[0], end_point[0]), max(start_point[1], end_point[1])
                
                # Only add ROI if it has reasonable size
                if abs(x2 - x1) > 20 and abs(y2 - y1) > 20:
                    new_roi = {
                        'id': len(rois),
                        'name': f'Protein Container {len(rois)+1}',
                        'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                        'description': f'Protein container area {len(rois)+1}'
                    }
                    rois.append(new_roi)
                    print(f"✅ Added ROI {len(rois)}: ({x1},{y1}) to ({x2},{y2})")
                else:
                    print("❌ ROI too small, please draw larger area")
                
                start_point = None
                end_point = None
    
    window_name = f"ROI Selector - {os.path.basename(video_path)}"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, mouse_callback)
    
    # Start at a frame that likely shows the action
    current_frame = min(150, total_frames // 4)  # Start at 25% of video
    
    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        ret, frame = cap.read()
        if not ret:
            break
        
        # Draw ROIs on frame
        display_frame = draw_roi_on_frame(frame, rois, None, drawing, start_point, end_point)
        
        # Add frame info and instructions
        cv2.putText(display_frame, f"Frame: {current_frame}/{total_frames}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display_frame, f"ROIs: {len(rois)}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display_frame, "Click & drag to create ROI", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(display_frame, "n=next, p=prev, s=save, q=quit, r=reset", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        cv2.imshow(window_name, display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('n'):
            current_frame = min(current_frame + 30, total_frames - 1)  # Skip 1 second
            print(f"📹 Frame: {current_frame}")
        elif key == ord('p'):
            current_frame = max(current_frame - 30, 0)  # Go back 1 second
            print(f"📹 Frame: {current_frame}")
        elif key == ord('s'):
            if len(rois) > 0:
                # Save ROIs
                roi_data = {
                    "video_name": os.path.splitext(os.path.basename(video_path))[0],
                    "created_at": datetime.now().isoformat(),
                    "description": f"ROIs for {os.path.basename(video_path)} - Define protein container areas where scooper is required",
                    "rois": rois
                }
                
                with open(output_path, 'w') as f:
                    json.dump(roi_data, f, indent=2)
                
                print(f"\n✅ ROIs saved to: {output_path}")
                print(f"📊 Created {len(rois)} ROIs:")
                for i, roi in enumerate(rois):
                    print(f"   ROI {i+1}: ({roi['x1']},{roi['y1']}) to ({roi['x2']},{roi['y2']})")
                break
            else:
                print("❌ No ROIs created yet! Please draw at least one ROI.")
        elif key == ord('q'):
            print("❌ Quitting without saving ROIs")
            break
        elif key == ord('r'):
            rois = []
            print("🔄 Reset all ROIs")
    
    cap.release()
    cv2.destroyAllWindows()
    return len(rois) > 0

def main():
    print("Manual ROI Selector for Pizza Scooper Violation Detection")
    print("=" * 70)
    print("This tool helps you create ROIs for each video manually.")
    print("You will need to watch each video and draw ROIs around protein containers.")
    print("=" * 70)
    
    videos = [
        "data/videos/Sah b3dha ghalt.mp4",
        "data/videos/Sah w b3dha ghalt (2).mp4", 
        "data/videos/Sah w b3dha ghalt (3).mp4"
    ]
    
    for i, video_path in enumerate(videos, 1):
        if os.path.exists(video_path):
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = f"data/rois/{video_name}_rois.json"
            
            print(f"\n🎬 VIDEO {i}/3: {video_name}")
            print("=" * 50)
            
            # Check if ROIs already exist
            if os.path.exists(output_path):
                print(f"⚠️  ROIs already exist for {video_name}")
                response = input("Do you want to recreate them? (y/n): ").lower().strip()
                if response != 'y':
                    print(f"⏭️  Skipping {video_name}")
                    continue
            
            if select_rois_for_video(video_path, output_path):
                print(f"✅ Successfully created ROIs for {video_name}")
            else:
                print(f"❌ Failed to create ROIs for {video_name}")
        else:
            print(f"❌ Video not found: {video_path}")
    
    print("\n" + "=" * 70)
    print("🎉 ROI Creation Complete!")
    print("You can now run the video testing:")
    print("python test_all_videos_correct_logic.py")

if __name__ == "__main__":
    main() 