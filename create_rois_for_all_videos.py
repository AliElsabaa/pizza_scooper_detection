"""
ROI Creation Tool for All Videos
This script helps create proper ROIs for each video by extracting sample frames.
"""

import cv2
import json
import os
from datetime import datetime

def extract_sample_frames(video_path, output_dir, num_frames=5):
    """Extract sample frames from video for ROI creation"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Could not open video: {video_path}")
        return False
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps
    
    print(f"Video: {os.path.basename(video_path)}")
    print(f"Total frames: {total_frames}, FPS: {fps:.2f}, Duration: {duration:.2f}s")
    
    # Extract frames at regular intervals
    frame_indices = [int(total_frames * i / num_frames) for i in range(num_frames)]
    
    os.makedirs(output_dir, exist_ok=True)
    
    for i, frame_idx in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            frame_path = os.path.join(output_dir, f"frame_{i+1}_{frame_idx}.jpg")
            cv2.imwrite(frame_path, frame)
            print(f"Saved frame {i+1}: {frame_path}")
    
    cap.release()
    return True

def create_roi_template(video_name, rois):
    """Create ROI template for a video"""
    template = {
        "video_name": video_name,
        "created_at": datetime.now().isoformat(),
        "description": f"ROIs for {video_name} - Define protein container areas where scooper is required",
        "rois": rois
    }
    return template

def main():
    print("ROI Creation Tool for Pizza Scooper Violation Detection")
    print("=" * 60)
    
    videos = [
        "data/videos/Sah b3dha ghalt.mp4",
        "data/videos/Sah w b3dha ghalt (2).mp4", 
        "data/videos/Sah w b3dha ghalt (3).mp4"
    ]
    
    # Extract sample frames for each video
    for video_path in videos:
        if os.path.exists(video_path):
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_dir = f"data/rois/{video_name}_frames"
            
            print(f"\nProcessing: {video_name}")
            print("-" * 40)
            
            if extract_sample_frames(video_path, output_dir):
                print(f"Sample frames extracted to: {output_dir}")
                print("Please use the ROI tool to create ROIs for this video:")
                print(f"python roi_tool/draw_roi.py --input_dir {output_dir} --output data/rois/{video_name}_rois.json")
            else:
                print(f"Failed to extract frames from {video_path}")
        else:
            print(f"Video not found: {video_path}")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Run the ROI tool for each video to create proper ROIs")
    print("2. Use the created ROIs in the testing scripts")
    print("3. Test with the correct violation logic")

if __name__ == "__main__":
    main() 