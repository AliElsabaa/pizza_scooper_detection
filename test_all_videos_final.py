"""
Final Optimized Video Testing for Pizza Scooper Violation Detection
This script uses the most refined violation detection logic to achieve optimal accuracy.
"""

import cv2
import json
import numpy as np
from ultralytics import YOLO
import os
import time
from datetime import datetime
from collections import deque

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

class OptimizedViolationDetector:
    def __init__(self, confidence_threshold=0.7, temporal_window=60, min_violation_duration=30):
        self.confidence_threshold = confidence_threshold
        self.temporal_window = temporal_window
        self.min_violation_duration = min_violation_duration
        self.violation_history = deque(maxlen=temporal_window)
        self.violation_count = 0
        self.last_violation_frame = -1
        self.violation_start_frame = -1
        self.current_violation_duration = 0
        
    def detect_violations(self, frame_detections, frame_number):
        """Detect violations with advanced temporal smoothing"""
        # Filter detections by confidence
        high_conf_detections = [
            det for det in frame_detections 
            if det['score'] >= self.confidence_threshold
        ]
        
        # Check for violations in this frame
        frame_violations = []
        for idx, roi in enumerate(self.rois):
            hand_in_roi = False
            scooper_in_roi = False
            
            for det in high_conf_detections:
                if is_in_roi(det["bbox"], [roi]) is not None:
                    if det["label"].lower() == "hand":
                        hand_in_roi = True
                    if det["label"].lower() == "scooper":
                        scooper_in_roi = True
            
            if hand_in_roi and not scooper_in_roi:
                frame_violations.append({"roi_id": idx, "type": "no_scooper"})
        
        # Advanced temporal smoothing
        is_new_violation = False
        
        if frame_violations:
            # Check if we're in an ongoing violation
            if self.violation_start_frame == -1:
                # Start new violation
                self.violation_start_frame = frame_number
                self.current_violation_duration = 1
            else:
                # Continue existing violation
                self.current_violation_duration += 1
        else:
            # No violation in this frame
            if self.violation_start_frame != -1:
                # Check if the violation was long enough to count
                if self.current_violation_duration >= self.min_violation_duration:
                    # Check if we had a recent violation (avoid double counting)
                    recent_violations = sum(1 for v in self.violation_history if v > 0)
                    if recent_violations == 0:
                        is_new_violation = True
                        self.violation_count += 1
                        self.last_violation_frame = frame_number
                        print(f"    VIOLATION CONFIRMED: Duration {self.current_violation_duration} frames")
                
                # Reset violation tracking
                self.violation_start_frame = -1
                self.current_violation_duration = 0
        
        # Update history
        self.violation_history.append(len(frame_violations))
        
        return frame_violations, is_new_violation
    
    def set_rois(self, rois):
        """Set ROIs for violation detection"""
        self.rois = rois

def test_video_final(video_path, expected_violations, model, rois):
    """Test a single video with final optimized violation detection"""
    print(f"\nTesting video: {os.path.basename(video_path)}")
    print(f"Expected violations: {expected_violations}")
    print("-" * 60)
    
    # Initialize violation detector with optimized parameters
    detector = OptimizedViolationDetector(
        confidence_threshold=0.7,  # Higher confidence threshold
        temporal_window=90,        # 3 seconds at 30fps
        min_violation_duration=45  # 1.5 seconds minimum violation duration
    )
    detector.set_rois(rois)
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"ERROR: Could not open video {video_path}")
        return 0, 0, 0
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0
    
    print(f"Video properties:")
    print(f"  - Total frames: {total_frames}")
    print(f"  - FPS: {fps:.1f}")
    print(f"  - Duration: {duration:.1f} seconds")
    print(f"  - Confidence threshold: {detector.confidence_threshold}")
    print(f"  - Temporal window: {detector.temporal_window} frames ({detector.temporal_window/fps:.1f}s)")
    print(f"  - Min violation duration: {detector.min_violation_duration} frames ({detector.min_violation_duration/fps:.1f}s)")
    
    # Process all frames
    frame_count = 0
    violation_frames = []
    detection_stats = {"hand": 0, "scooper": 0, "person": 0, "pizza": 0}
    high_conf_detections = 0
    
    print(f"\nProcessing frames...")
    start_time = time.time()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Run detection
        results = model(frame)
        detections = []
        
        # Parse results
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
                    
                    # Update detection stats
                    if label.lower() in detection_stats:
                        detection_stats[label.lower()] += 1
                    
                    # Count high confidence detections
                    if float(conf) >= detector.confidence_threshold:
                        high_conf_detections += 1
        
        # Detect violations with advanced temporal smoothing
        frame_violations, is_new_violation = detector.detect_violations(detections, frame_count)
        
        # Log new violations
        if is_new_violation:
            violation_frames.append({
                "frame": frame_count,
                "violations": frame_violations,
                "detections": len(detections),
                "high_conf_detections": sum(1 for d in detections if d['score'] >= detector.confidence_threshold)
            })
            print(f"  Frame {frame_count}: NEW VIOLATION detected (total: {detector.violation_count})")
        
        # Progress indicator
        if frame_count % 100 == 0:
            elapsed = time.time() - start_time
            fps_processed = frame_count / elapsed
            print(f"  Processed {frame_count}/{total_frames} frames ({fps_processed:.1f} fps)")
    
    cap.release()
    
    # Check for any ongoing violation at the end
    if detector.violation_start_frame != -1 and detector.current_violation_duration >= detector.min_violation_duration:
        recent_violations = sum(1 for v in detector.violation_history if v > 0)
        if recent_violations == 0:
            detector.violation_count += 1
            print(f"  Final violation confirmed: Duration {detector.current_violation_duration} frames")
    
    # Calculate processing time
    total_time = time.time() - start_time
    avg_fps = frame_count / total_time
    
    # Results
    print(f"\nResults for {os.path.basename(video_path)}:")
    print(f"  - Frames processed: {frame_count}")
    print(f"  - Processing time: {total_time:.1f} seconds")
    print(f"  - Average FPS: {avg_fps:.1f}")
    print(f"  - Total violations detected: {detector.violation_count}")
    print(f"  - Expected violations: {expected_violations}")
    
    # Detection statistics
    print(f"  - Detection statistics:")
    for obj, count in detection_stats.items():
        print(f"    {obj}: {count}")
    print(f"  - High confidence detections: {high_conf_detections}")
    
    # Violation accuracy
    accuracy = "CORRECT" if detector.violation_count == expected_violations else "INCORRECT"
    print(f"  - Violation accuracy: {accuracy}")
    
    if violation_frames:
        print(f"  - Violation frames: {len(violation_frames)}")
        for vf in violation_frames[:3]:  # Show first 3 violation frames
            print(f"    Frame {vf['frame']}: {len(vf['violations'])} violation(s), {vf['high_conf_detections']} high-conf detections")
        if len(violation_frames) > 3:
            print(f"    ... and {len(violation_frames) - 3} more")
    
    return detector.violation_count, expected_violations, accuracy == "CORRECT"

def main():
    print("=" * 80)
    print("FINAL OPTIMIZED VIDEO TESTING FOR PIZZA SCOOPER VIOLATION DETECTION")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Load model and ROIs
    print("Loading components...")
    model_path = "model/yolo12m-v2.pt"
    if not os.path.exists(model_path):
        print(f"ERROR: Model not found at {model_path}")
        return
    
    model = YOLO(model_path)
    print("YOLO model loaded successfully")
    
    rois = load_rois()
    print(f"Loaded {len(rois)} ROIs")
    
    # Define test videos and expected violations
    test_videos = [
        ("data/videos/Sah w b3dha ghalt.mp4", 1),
        ("data/videos/Sah w b3dha ghalt (2).mp4", 2),
        ("data/videos/Sah w b3dha ghalt (3).mp4", 1)
    ]
    
    # Test each video
    results = []
    total_correct = 0
    
    for video_path, expected_violations in test_videos:
        if not os.path.exists(video_path):
            print(f"ERROR: Video not found: {video_path}")
            continue
        
        detected_violations, expected, is_correct = test_video_final(video_path, expected_violations, model, rois)
        results.append({
            "video": os.path.basename(video_path),
            "detected": detected_violations,
            "expected": expected,
            "correct": is_correct
        })
        
        if is_correct:
            total_correct += 1
    
    # Summary report
    print("\n" + "=" * 80)
    print("FINAL OPTIMIZED TEST SUMMARY")
    print("=" * 80)
    
    print(f"Videos tested: {len(results)}")
    print(f"Correct predictions: {total_correct}/{len(results)}")
    print(f"Overall accuracy: {total_correct/len(results)*100:.1f}%")
    
    print(f"\nDetailed Results:")
    for result in results:
        status = "PASS" if result["correct"] else "FAIL"
        print(f"  {result['video']}: {result['detected']}/{result['expected']} violations - {status}")
    
    # Recommendations
    print(f"\nRecommendations:")
    if total_correct == len(results):
        print("EXCELLENT! All videos tested correctly!")
        print("Your violation detection system is working perfectly.")
        print("The optimized logic correctly identifies violations in all test videos.")
    elif total_correct > 0:
        print("PARTIAL SUCCESS! Some videos tested correctly.")
        print("Check the failed videos for potential issues:")
        print("   - ROI positioning might need adjustment")
        print("   - Violation timing might be different than expected")
        print("   - Model might need retraining or fine-tuning")
    else:
        print("NEEDS WORK! No videos tested correctly.")
        print("Potential issues to investigate:")
        print("   - ROI coordinates might be incorrect")
        print("   - Violation detection logic might need refinement")
        print("   - Model might need retraining or fine-tuning")
        print("   - Try adjusting confidence threshold or temporal parameters")
    
    # Save detailed report
    report_filename = f"final_video_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_filename, 'w') as f:
        f.write("FINAL OPTIMIZED VIDEO TESTING REPORT\n")
        f.write("=" * 50 + "\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Videos tested: {len(results)}\n")
        f.write(f"Correct predictions: {total_correct}/{len(results)}\n")
        f.write(f"Overall accuracy: {total_correct/len(results)*100:.1f}%\n\n")
        
        f.write("DETAILED RESULTS:\n")
        for result in results:
            status = "PASS" if result["correct"] else "FAIL"
            f.write(f"  {result['video']}: {result['detected']}/{result['expected']} violations - {status}\n")
    
    print(f"\nDetailed report saved to: {report_filename}")
    
    return total_correct == len(results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 