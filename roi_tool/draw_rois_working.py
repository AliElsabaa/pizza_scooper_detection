"""
Working ROI Drawing Tool for All Videos
Simple and reliable version.
"""

import cv2
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
VIDEOS = [
    'Sah w b3dha ghalt.mp4',
    'Sah w b3dha ghalt (2).mp4',
    'Sah w b3dha ghalt (3).mp4'
]

def draw_rois_simple(frame, video_name):
    """Simple ROI drawing without complex mouse callbacks"""
    rois = []
    clone = frame.copy()
    
    window_name = f"Draw ROIs - {video_name}"
    cv2.namedWindow(window_name)
    
    print(f"\n{'='*60}")
    print(f"Drawing ROIs for: {video_name}")
    print(f"{'='*60}")
    print("Instructions:")
    print("1. Click and drag to draw rectangles around protein containers")
    print("2. Press 'q' to finish and save")
    print("3. Press 'r' to reset all ROIs")
    print("4. Focus on areas where workers grab ingredients!")
    print(f"{'='*60}")
    
    # Simple mouse callback
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            param['start_point'] = (x, y)
            param['drawing'] = True
        elif event == cv2.EVENT_MOUSEMOVE and param['drawing']:
            param['current_point'] = (x, y)
        elif event == cv2.EVENT_LBUTTONUP and param['drawing']:
            param['drawing'] = False
            start = param['start_point']
            end = (x, y)
            
            # Ensure proper rectangle coordinates
            x1, y1 = min(start[0], end[0]), min(start[1], end[1])
            x2, y2 = max(start[0], end[0]), max(start[1], end[1])
            
            # Only add if rectangle is reasonable size
            if abs(x2 - x1) > 20 and abs(y2 - y1) > 20:
                rois.append((x1, y1, x2, y2))
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                print(f"✅ Added ROI {len(rois)}: ({x1},{y1}) to ({x2},{y2})")
            
            param['start_point'] = None
            param['current_point'] = None
    
    # Mouse state
    mouse_state = {'drawing': False, 'start_point': None, 'current_point': None}
    cv2.setMouseCallback(window_name, mouse_callback, mouse_state)
    
    while True:
        temp = frame.copy()
        
        # Draw current selection
        if mouse_state['drawing'] and mouse_state['start_point'] and mouse_state['current_point']:
            cv2.rectangle(temp, mouse_state['start_point'], mouse_state['current_point'], (255, 0, 0), 1)
        
        # Add instructions on frame
        cv2.putText(temp, f"Video: {video_name}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(temp, f"ROIs drawn: {len(rois)}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(temp, "Click & drag to draw ROI", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(temp, "q=finish, r=reset", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        cv2.imshow(window_name, temp)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('r'):
            frame[:] = clone.copy()
            rois.clear()
            print("🔄 Reset all ROIs")

    cv2.destroyAllWindows()
    return rois

def main():
    print("Working ROI Drawing Tool for All Videos")
    print("=" * 50)
    print("This tool will help you draw ROIs for all three videos.")
    print("=" * 50)
    
    for i, video_file in enumerate(VIDEOS, 1):
        video_path = os.path.join(DATA_DIR, 'videos', video_file)
        video_name = os.path.splitext(video_file)[0]
        roi_save_path = os.path.join(DATA_DIR, 'rois', f'{video_name}_rois.json')
        
        print(f"\n🎬 Processing VIDEO {i}/3: {video_name}")
        print("-" * 40)
        
        if not os.path.exists(video_path):
            print(f"❌ Video not found: {video_path}")
            continue
            
        # Check if ROIs already exist
        if os.path.exists(roi_save_path):
            print(f"⚠️  ROIs already exist for {video_name}")
            response = input("Do you want to recreate them? (y/n): ").lower().strip()
            if response != 'y':
                print(f"⏭️  Skipping {video_name}")
                continue
        
        # Read first frame from video
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print(f"❌ Failed to read frame from {video_name}")
            continue
            
        print(f"✅ Loaded frame from {video_name}")
        
        # Draw ROIs
        rois = draw_rois_simple(frame, video_name)
        
        if rois:
            # Save ROIs
            os.makedirs(os.path.dirname(roi_save_path), exist_ok=True)
            
            roi_data = {
                "video_name": video_name,
                "created_at": "2025-01-20T12:00:00",
                "description": f"ROIs for {video_name} - Define protein container areas where scooper is required",
                "rois": [{'x1': r[0], 'y1': r[1], 'x2': r[2], 'y2': r[3]} for r in rois]
            }
            
            with open(roi_save_path, 'w') as f:
                json.dump(roi_data, f, indent=2)
            
            print(f"✅ Saved {len(rois)} ROIs to {roi_save_path}")
            
            # Show ROI details
            for j, roi in enumerate(rois):
                print(f"   ROI {j+1}: ({roi[0]},{roi[1]}) to ({roi[2]},{roi[3]})")
        else:
            print(f"❌ No ROIs created for {video_name}")
        
        # Continue to next video
        if i < len(VIDEOS):
            print(f"\n⏭️  Continuing to next video in 3 seconds...")
            import time
            time.sleep(3)
    
    print("\n" + "=" * 50)
    print("🎉 ROI Creation Complete!")
    print("You can now run the video testing:")
    print("scooperenv\\Scripts\\python.exe test_all_videos_correct_logic.py")

if __name__ == "__main__":
    main() 