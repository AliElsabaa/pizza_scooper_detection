"""
Create Default ROIs for All Videos
This script creates reasonable default ROIs for testing the violation detection system.
"""

import json
import os
from datetime import datetime

def create_default_rois_for_video(video_name, frame_width=1280, frame_height=720):
    """Create reasonable default ROIs for a video"""
    
    # Define typical protein container areas (adjust these based on your videos)
    if "Sah b3dha ghalt" in video_name and "(2)" not in video_name and "(3)" not in video_name:
        # Video 1: Sah b3dha ghalt.mp4
        rois = [
            {
                "id": 0,
                "name": "Protein Container 1",
                "x1": 400,
                "y1": 200,
                "x2": 600,
                "y2": 350,
                "description": "Main protein container area"
            },
            {
                "id": 1,
                "name": "Protein Container 2",
                "x1": 650,
                "y1": 200,
                "x2": 850,
                "y2": 350,
                "description": "Secondary protein container area"
            }
        ]
    elif "(2)" in video_name:
        # Video 2: Sah w b3dha ghalt (2).mp4
        rois = [
            {
                "id": 0,
                "name": "Protein Container 1",
                "x1": 350,
                "y1": 180,
                "x2": 550,
                "y2": 330,
                "description": "Main protein container area"
            },
            {
                "id": 1,
                "name": "Protein Container 2",
                "x1": 600,
                "y1": 180,
                "x2": 800,
                "y2": 330,
                "description": "Secondary protein container area"
            }
        ]
    elif "(3)" in video_name:
        # Video 3: Sah w b3dha ghalt (3).mp4
        rois = [
            {
                "id": 0,
                "name": "Protein Container 1",
                "x1": 450,
                "y1": 220,
                "x2": 650,
                "y2": 370,
                "description": "Main protein container area"
            },
            {
                "id": 1,
                "name": "Protein Container 2",
                "x1": 700,
                "y1": 220,
                "x2": 900,
                "y2": 370,
                "description": "Secondary protein container area"
            }
        ]
    else:
        # Generic ROIs
        rois = [
            {
                "id": 0,
                "name": "Protein Container 1",
                "x1": 400,
                "y1": 200,
                "x2": 600,
                "y2": 350,
                "description": "Main protein container area"
            },
            {
                "id": 1,
                "name": "Protein Container 2",
                "x1": 650,
                "y1": 200,
                "x2": 850,
                "y2": 350,
                "description": "Secondary protein container area"
            }
        ]
    
    return rois

def main():
    print("Create Default ROIs for All Videos")
    print("=" * 50)
    print("This script creates reasonable default ROIs for testing.")
    print("=" * 50)
    
    videos = [
        "Sah b3dha ghalt",
        "Sah w b3dha ghalt (2)",
        "Sah w b3dha ghalt (3)"
    ]
    
    successful_rois = 0
    
    for i, video_name in enumerate(videos, 1):
        print(f"\n🎬 Processing VIDEO {i}/3: {video_name}")
        print("-" * 40)
        
        # Create ROI file path
        roi_save_path = f"data/rois/{video_name}_rois.json"
        
        # Create default ROIs
        rois = create_default_rois_for_video(video_name)
        
        # Create ROI data structure
        roi_data = {
            "video_name": video_name,
            "created_at": datetime.now().isoformat(),
            "description": f"Default ROIs for {video_name} - Define protein container areas where scooper is required",
            "rois": rois
        }
        
        # Save ROIs
        os.makedirs(os.path.dirname(roi_save_path), exist_ok=True)
        
        with open(roi_save_path, 'w') as f:
            json.dump(roi_data, f, indent=2)
        
        print(f"✅ Created {len(rois)} default ROIs for {video_name}")
        print(f"📁 Saved to: {roi_save_path}")
        
        # Show ROI details
        for j, roi in enumerate(rois):
            print(f"   ROI {j+1}: ({roi['x1']},{roi['y1']}) to ({roi['x2']},{roi['y2']})")
        
        successful_rois += 1
    
    print("\n" + "=" * 50)
    print("🎉 Default ROIs Created Successfully!")
    print(f"Created ROIs for {successful_rois}/{len(videos)} videos")
    print("\n📝 Note: These are default ROIs. You may need to adjust them manually")
    print("   by editing the JSON files if they don't match your video content.")
    print("\n✅ You can now run the video testing:")
    print("python test_all_videos_correct_logic.py")

if __name__ == "__main__":
    main() 