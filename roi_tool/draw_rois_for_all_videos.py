"""
ROI Drawing Tool for All Videos
Uses the same approach as draw_roi.py but for all three videos.
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

def draw_rois(frame, video_name):
    rois = []
    clone = frame.copy()
    roi = []
    drawing = [False]

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            roi.clear()
            roi.extend([x, y])
            drawing[0] = True
        elif event == cv2.EVENT_LBUTTONUP:
            roi.extend([x, y])
            drawing[0] = False
            rois.append(tuple(roi))
            cv2.rectangle(frame, (roi[0], roi[1]), (roi[2], roi[3]), (0, 255, 0), 2)

    window_name = f"Draw ROIs - {video_name}"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback)

    print(f"\n{'='*60}")
    print(f"Drawing ROIs for: {video_name}")
    print(f"{'='*60}")
    print("Instructions:")
    print("1. Click and drag to draw rectangles around protein containers")
    print("2. Press 'q' to finish and save")
    print("3. Press 'r' to reset all ROIs")
    print("4. Focus on areas where workers grab ingredients!")
    print(f"{'='*60}")

    while True:
        temp = frame.copy()
        if drawing[0] and len(roi) == 2:
            cv2.rectangle(temp, (roi[0], roi[1]), (roi[2], roi[3]), (255, 0, 0), 1)
        
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
    print("ROI Drawing Tool for All Videos")
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
        rois = draw_rois(frame, video_name)
        
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
    print("python test_all_videos_correct_logic.py")

if __name__ == "__main__":
    main() 