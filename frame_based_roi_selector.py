"""
Frame-Based ROI Selector for Pizza Scooper Violation Detection
This script saves sample frames and allows manual ROI specification without GUI.
"""

import cv2
import json
import os
import numpy as np
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
    
    frame_paths = []
    for i, frame_idx in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            frame_path = os.path.join(output_dir, f"frame_{i+1}_{frame_idx}.jpg")
            cv2.imwrite(frame_path, frame)
            frame_paths.append(frame_path)
            print(f"Saved frame {i+1}: {frame_path}")
    
    cap.release()
    return frame_paths

def get_roi_coordinates_manual(video_name, frame_paths):
    """Get ROI coordinates manually from user"""
    print(f"\n{'='*60}")
    print(f"MANUAL ROI SELECTION FOR: {video_name}")
    print(f"{'='*60}")
    print("I will show you sample frames and you can specify ROI coordinates.")
    print("For each ROI, provide: x1, y1, x2, y2 (top-left to bottom-right)")
    print("Press Enter to skip a frame if no ROIs needed.")
    print(f"{'='*60}")
    
    rois = []
    
    for i, frame_path in enumerate(frame_paths):
        print(f"\n📷 Frame {i+1}: {os.path.basename(frame_path)}")
        print("Frame saved at:", frame_path)
        print("You can open this image to see the frame.")
        
        while True:
            try:
                response = input("Enter ROI coordinates (x1,y1,x2,y2) or 'skip' or 'done': ").strip().lower()
                
                if response == 'skip':
                    print("Skipping this frame...")
                    break
                elif response == 'done':
                    print("Finished ROI selection.")
                    return rois
                elif response == '':
                    print("Skipping this frame...")
                    break
                else:
                    # Parse coordinates
                    coords = [int(x.strip()) for x in response.split(',')]
                    if len(coords) == 4:
                        x1, y1, x2, y2 = coords
                        if x1 < x2 and y1 < y2:  # Ensure valid rectangle
                            new_roi = {
                                'id': len(rois),
                                'name': f'Protein Container {len(rois)+1}',
                                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                                'description': f'Protein container area {len(rois)+1} from frame {i+1}'
                            }
                            rois.append(new_roi)
                            print(f"✅ Added ROI {len(rois)}: ({x1},{y1}) to ({x2},{y2})")
                            break
                        else:
                            print("❌ Invalid coordinates: x1,y1 should be top-left, x2,y2 should be bottom-right")
                    else:
                        print("❌ Invalid format. Use: x1,y1,x2,y2")
            except ValueError:
                print("❌ Invalid input. Please enter numbers separated by commas.")
            except KeyboardInterrupt:
                print("\n❌ Interrupted by user.")
                return rois
    
    return rois

def create_roi_from_coordinates(video_name, rois):
    """Create ROI configuration from coordinates"""
    roi_data = {
        "video_name": video_name,
        "created_at": datetime.now().isoformat(),
        "description": f"ROIs for {video_name} - Define protein container areas where scooper is required",
        "rois": rois
    }
    return roi_data

def main():
    print("Frame-Based ROI Selector for Pizza Scooper Violation Detection")
    print("=" * 70)
    print("This tool extracts sample frames and allows manual ROI specification.")
    print("=" * 70)
    
    videos = [
        "data/videos/Sah b3dha ghalt.mp4",
        "data/videos/Sah w b3dha ghalt (2).mp4", 
        "data/videos/Sah w b3dha ghalt (3).mp4"
    ]
    
    successful_rois = 0
    
    for i, video_path in enumerate(videos, 1):
        if os.path.exists(video_path):
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = f"data/rois/{video_name}_rois.json"
            frames_dir = f"data/rois/{video_name}_frames"
            
            print(f"\n🎬 Processing VIDEO {i}/3: {video_name}")
            print("=" * 50)
            
            # Extract sample frames
            print("Extracting sample frames...")
            frame_paths = extract_sample_frames(video_path, frames_dir)
            
            if frame_paths:
                print(f"✅ Extracted {len(frame_paths)} sample frames")
                
                # Get ROI coordinates manually
                rois = get_roi_coordinates_manual(video_name, frame_paths)
                
                if rois:
                    # Save ROI configuration
                    roi_data = create_roi_from_coordinates(video_name, rois)
                    
                    with open(output_path, 'w') as f:
                        json.dump(roi_data, f, indent=2)
                    
                    print(f"\n✅ ROIs saved to: {output_path}")
                    print(f"📊 Created {len(rois)} ROIs:")
                    for j, roi in enumerate(rois):
                        print(f"   ROI {j+1}: ({roi['x1']},{roi['y1']}) to ({roi['x2']},{roi['y2']})")
                    
                    successful_rois += 1
                else:
                    print("❌ No ROIs created for this video")
            else:
                print("❌ Failed to extract frames from video")
        else:
            print(f"❌ Video not found: {video_path}")
    
    print("\n" + "=" * 70)
    print("🎉 ROI Creation Complete!")
    print(f"Successfully created ROIs for {successful_rois}/{len(videos)} videos")
    
    if successful_rois == len(videos):
        print("\n✅ All ROIs created successfully!")
        print("You can now run the video testing:")
        print("python test_all_videos_correct_logic.py")
    else:
        print(f"\n⚠️  Only {successful_rois}/{len(videos)} videos have ROIs")
        print("Please run the script again to create missing ROIs")

if __name__ == "__main__":
    main() 