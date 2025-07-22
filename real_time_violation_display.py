"""
Real-Time Violation Display for Pizza Scooper Violation Detection
This script demonstrates the real production workflow with ROI overlays and violation counts.
"""

import cv2
import json
import numpy as np
from ultralytics import YOLO
import os
import time
from collections import deque

def load_rois_for_video(video_name):
    """Load ROIs for specific video"""
    roi_path = f"data/rois/{video_name}_rois.json"
    if os.path.exists(roi_path):
        with open(roi_path, 'r') as f:
            roi_data = json.load(f)
            if isinstance(roi_data, dict):
                return roi_data.get('rois', [])
            else:
                return roi_data
    else:
        default_roi_path = "data/rois/rois.json"
        if os.path.exists(default_roi_path):
            with open(default_roi_path, 'r') as f:
                roi_data = json.load(f)
                if isinstance(roi_data, dict):
                    return roi_data.get('rois', [])
                else:
                    return roi_data
        return []

def is_in_roi(bbox, rois):
    """Check if a bbox is inside any ROI"""
    x1, y1, x2, y2 = bbox
    for idx, roi in enumerate(rois):
        rx1, ry1, rx2, ry2 = roi['x1'], roi['y1'], roi['x2'], roi['y2']
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        if rx1 <= cx <= rx2 and ry1 <= cy <= ry2:
            return idx
    return None

def draw_detections_and_rois(frame, detections, rois, violations_count, frame_info):
    """Draw detections, ROIs, and violation count on frame"""
    frame_copy = frame.copy()
    
    # Draw ROIs
    for i, roi in enumerate(rois):
        cv2.rectangle(frame_copy, (roi['x1'], roi['y1']), (roi['x2'], roi['y2']), (0, 255, 0), 2)
    
    # Draw detections
    for detection in detections:
        bbox = detection['bbox']
        class_id = detection['class_id']
        confidence = detection['confidence']
        
        # Color coding for different classes
        colors = {
            0: (255, 0, 0),    # hand - blue
            1: (255, 255, 0),  # person - cyan
            2: (0, 0, 255),    # pizza - red
            3: (0, 255, 255)   # scooper - yellow
        }
        
        color = colors.get(class_id, (255, 255, 255))
        cv2.rectangle(frame_copy, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
    
    # Draw violation count (top-left corner)
    cv2.rectangle(frame_copy, (10, 10), (300, 100), (0, 0, 0), -1)
    cv2.rectangle(frame_copy, (10, 10), (300, 100), (255, 255, 255), 2)
    cv2.putText(frame_copy, "VIOLATIONS DETECTED", (20, 35), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame_copy, f"Count: {violations_count}", (20, 65), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0) if violations_count == 0 else (0, 0, 255), 2)
    
    return frame_copy

def iou(boxA, boxB):
    # Compute the intersection over union of two boxes
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    iou = interArea / float(boxAArea + boxBArea - interArea + 1e-6)
    return iou

def draw_flag_on_frame(frame, hand_states):
    # Draw each hand's flag stacked vertically, left of the right edge
    h, w = frame.shape[:2]
    x = w - 350  # Move left for visibility
    y_start = h // 2 - 40
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.1
    thickness = 3
    color_outline = (0, 0, 0)
    color_fill = (255, 0, 255)  # Bright magenta
    for i, (hid, state) in enumerate(hand_states.items()):
        flag_text = f"{hid}: {state['flag']}"
        y = y_start + i * 40
        # Draw outline
        cv2.putText(frame, flag_text, (x, y), font, font_scale, color_outline, thickness + 2, cv2.LINE_AA)
        # Draw fill
        cv2.putText(frame, flag_text, (x, y), font, font_scale, color_fill, thickness, cv2.LINE_AA)
    return frame

def detect_violations_realtime_state_machine_v2(frame_detections, rois, hand_states, frame_idx, fps):
    """
    Improved state machine:
    - Stack flag text for visibility
    - Add cooldown after violation
    - Only raise violation if hand is with pizza for continuous 1000ms
    - Stricter IOU/timing checks
    """
    violations = []
    hands = [d for d in frame_detections if d['class_id'] == 0 and d['confidence'] > 0.5]
    scoopers = [d for d in frame_detections if d['class_id'] == 3 and d['confidence'] > 0.5]
    pizzas = [d for d in frame_detections if d['class_id'] == 2 and d['confidence'] > 0.5]
    for idx, hand in enumerate(hands):
        hand_id = f"hand_{idx}"
        hand_box = hand['bbox']
        max_iou = 0
        roi_idx = None
        for i, roi in enumerate(rois):
            roi_box = [roi['x1'], roi['y1'], roi['x2'], roi['y2']]
            iou_val = iou(hand_box, roi_box)
            if iou_val > max_iou:
                max_iou = iou_val
                roi_idx = i
        in_roi = max_iou > 0.2
        with_scooper = any(iou(hand_box, s['bbox']) > 0.2 for s in scoopers)
        if hand_id not in hand_states:
            hand_states[hand_id] = {
                'flag': 'idle',
                'roi_idx': roi_idx,
                'entered_time': None,
                'left_time': None,
                'entry_with_scooper': False,
                'exit_with_scooper': False,
                'iou_high_start': None,
                'iou_high': False,
                'violation_raised': False,
                'entry_detected': False,
                'post_exit_timer': None,
                'pizza_continuous_start': None,
                'cooldown_until': None
            }
        state = hand_states[hand_id]
        # Cooldown: skip if in cooldown
        if state['cooldown_until'] and frame_idx < state['cooldown_until']:
            continue
        # Real-time entry detection
        if state['flag'] == 'idle':
            if in_roi:
                state['flag'] = 'entered'
                state['entered_time'] = frame_idx
                state['entry_with_scooper'] = with_scooper
                state['entry_detected'] = True
            else:
                state['entered_time'] = None
                state['entry_with_scooper'] = False
                state['entry_detected'] = False
        elif state['flag'] == 'entered':
            if not in_roi:
                state['flag'] = 'exited'
                state['left_time'] = frame_idx
                state['exit_with_scooper'] = with_scooper
                state['iou_high_start'] = None
                state['iou_high'] = False
                state['violation_raised'] = False
                state['post_exit_timer'] = None
                state['pizza_continuous_start'] = None
            elif with_scooper:
                state['entry_with_scooper'] = True
        elif state['flag'] == 'exited':
            # Case 1: Entered without scooper, exited without scooper → violation if goes to pizza for 1000ms continuous
            if not state['entry_with_scooper'] and not state['exit_with_scooper']:
                with_pizza = any(iou(hand_box, p['bbox']) > 0.2 for p in pizzas)
                if with_pizza:
                    if state['pizza_continuous_start'] is None:
                        state['pizza_continuous_start'] = frame_idx
                    elif frame_idx - state['pizza_continuous_start'] >= int(1.0 * fps):
                        if not state['violation_raised']:
                            violations.append({'type': 'hand_grabbed_without_scooper', 'frame': frame_idx, 'hand_id': hand_id})
                            state['violation_raised'] = True
                            state['flag'] = 'idle'
                            state['cooldown_until'] = frame_idx + int(1.0 * fps)  # 1s cooldown
                else:
                    state['pizza_continuous_start'] = None
            # Case 2: Entered without scooper, exited with scooper → no violation
            elif not state['entry_with_scooper'] and state['exit_with_scooper']:
                state['flag'] = 'idle'
            # Case 3: Entered with scooper, exited with scooper → no violation
            elif state['entry_with_scooper'] and state['exit_with_scooper']:
                state['flag'] = 'idle'
            # Case 4: Entered with scooper, exited without scooper
            elif state['entry_with_scooper'] and not state['exit_with_scooper']:
                if max_iou > 0.5:
                    if state['iou_high_start'] is None:
                        state['iou_high_start'] = frame_idx
                    elif frame_idx - state['iou_high_start'] >= int(0.5 * fps):
                        with_pizza = any(iou(hand_box, p['bbox']) > 0.2 for p in pizzas)
                        if with_pizza:
                            if state['pizza_continuous_start'] is None:
                                state['pizza_continuous_start'] = frame_idx
                            elif frame_idx - state['pizza_continuous_start'] >= int(1.0 * fps):
                                if not state['violation_raised']:
                                    violations.append({'type': 'hand_grabbed_without_scooper_after_scooper', 'frame': frame_idx, 'hand_id': hand_id})
                                    state['violation_raised'] = True
                                    state['flag'] = 'idle'
                                    state['cooldown_until'] = frame_idx + int(1.0 * fps)
                        else:
                            state['pizza_continuous_start'] = None
                else:
                    state['iou_high_start'] = None
                    state['pizza_continuous_start'] = None
                if state['iou_high_start'] and frame_idx - state['iou_high_start'] > int(1.0 * fps):
                    state['flag'] = 'idle'
            if in_roi:
                state['flag'] = 'entered'
                state['entered_time'] = frame_idx
                state['entry_with_scooper'] = with_scooper
                state['entry_detected'] = True
    return violations, hand_states

def run_realtime_display(video_path):
    """Run real-time violation display"""
    print(f"Starting real-time display for: {os.path.basename(video_path)}")
    print("Press 'q' to quit, 'p' to pause/resume")
    
    # Load model
    model = YOLO("model/yolo12m-v2.pt")
    
    # Load ROIs
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    rois = load_rois_for_video(video_name)
    print(f"Loaded {len(rois)} ROIs")
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Could not open video: {video_path}")
        return
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Prepare video writer for saving output
    output_path = os.path.join("output", f"annotated_{os.path.basename(video_path)}")
    os.makedirs("output", exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Initialize tracking
    hand_states = {}
    total_violations = 0
    paused = False
    
    # Constants for grace period and smoothing
    GRACE_PERIOD_MS = 1000  # 1 second grace period for missing objects
    CONSECUTIVE_MISSING_FRAMES = int(fps * 0.5)  # require 0.5 seconds of consecutive missing frames
    
    window_name = f"Real-Time Violation Detection - {os.path.basename(video_path)}"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    frame_count = 0
    start_time = time.time()
    
    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break
            frame_start = time.time()
            frame_detections = []
            
            # Use YOLO tracking with ByteTrack
            if frame_count % 3 == 0:
                results = model.track(frame, persist=True, tracker='bytetrack.yaml', verbose=False)
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            class_id = int(box.cls[0].cpu().numpy())
                            confidence = float(box.conf[0].cpu().numpy())
                            track_id = int(box.id[0].cpu().numpy()) if hasattr(box, 'id') and box.id is not None else None
                            frame_detections.append({
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'class_id': class_id,
                                'confidence': confidence,
                                'track_id': track_id,
                                'frame_time': time.time()
                            })
            
            # Process detections with grace period and smoothing
            hands = [d for d in frame_detections if d['class_id'] == 0 and d['confidence'] > 0.5]
            scoopers = [d for d in frame_detections if d['class_id'] == 3 and d['confidence'] > 0.5]
            pizzas = [d for d in frame_detections if d['class_id'] == 2 and d['confidence'] > 0.5]
            
            # Update object states with grace period
            current_time = time.time()
            for hand in hands:
                hand_id = f"hand_{hand['track_id']}" if hand['track_id'] is not None else f"hand_{hand['bbox']}"
                if hand_id not in hand_states:
                    hand_states[hand_id] = {
                        'entered_with_scooper': False,
                        'hand_in_roi': False,
                        'hand_entered_roi': False,
                        'last_seen_time': current_time,
                        'missing_frames_count': 0,
                        'last_position': hand['bbox'],
                        'violation_raised': False,
                        'entry_time': None,
                        'exit_time': None,
                        'scooper_present_at_entry': False,
                        'scooper_present_at_exit': False
                    }
                
                state = hand_states[hand_id]
                state['last_seen_time'] = current_time
                state['missing_frames_count'] = 0
                state['last_position'] = hand['bbox']
                
                # Calculate IOUs
                hand_roi_iou = max(iou(hand['bbox'], [roi['x1'], roi['y1'], roi['x2'], roi['y2']]) for roi in rois)
                scooper_roi_iou = 0
                for scooper in scoopers:
                    for roi in rois:
                        s_iou = iou(scooper['bbox'], [roi['x1'], roi['y1'], roi['x2'], roi['y2']])
                        if s_iou > scooper_roi_iou:
                            scooper_roi_iou = s_iou
                
                # Check if scooper touches pizza (for hard case)
                scooper_touched_pizza = False
                for scooper in scoopers:
                    for pizza in pizzas:
                        if iou(scooper['bbox'], pizza['bbox']) > 0.3:
                            scooper_touched_pizza = True
                            break
                    if scooper_touched_pizza:
                        break
                
                # Update hand_in_roi with grace period
                if hand_roi_iou > 0.2:
                    if not state['hand_entered_roi']:
                        # Hand just entered ROI
                        state['hand_entered_roi'] = True
                        state['entry_time'] = current_time
                        state['hand_in_roi'] = True
                        state['violation_raised'] = False
                        # Record if scooper was present at entry
                        state['scooper_present_at_entry'] = scooper_roi_iou > 0.2
                        state['entered_with_scooper'] = scooper_roi_iou > 0.2
                    else:
                        # Hand still in ROI
                        state['hand_in_roi'] = True
                elif current_time - state['last_seen_time'] > GRACE_PERIOD_MS / 1000:
                    state['missing_frames_count'] += 1
                    if state['missing_frames_count'] >= CONSECUTIVE_MISSING_FRAMES:
                        if state['hand_entered_roi']:
                            # Hand just exited ROI - make violation decision
                            state['exit_time'] = current_time
                            state['hand_entered_roi'] = False
                            state['hand_in_roi'] = False
                            state['scooper_present_at_exit'] = scooper_roi_iou > 0.2
                            
                            # Simple violation logic:
                            # Case 1: Entered without scooper, left without scooper = VIOLATION
                            if not state['scooper_present_at_entry'] and not state['scooper_present_at_exit']:
                                if not state['violation_raised']:
                                    total_violations += 1
                                    state['violation_raised'] = True
                            
                            # Case 2: Entered with scooper, left without scooper = VIOLATION (unless scooper touched pizza)
                            elif state['scooper_present_at_entry'] and not state['scooper_present_at_exit']:
                                if not scooper_touched_pizza and not state['violation_raised']:
                                    total_violations += 1
                                    state['violation_raised'] = True
                        else:
                            state['hand_in_roi'] = False
            
            # Clean up old states
            for hand_id in list(hand_states.keys()):
                if current_time - hand_states[hand_id]['last_seen_time'] > GRACE_PERIOD_MS / 1000:
                    del hand_states[hand_id]
            
            # Draw frame
            display_frame = draw_detections_and_rois(
                frame, frame_detections, rois, total_violations,
                {'frame': frame_count, 'fps': fps}
            )
            
            cv2.imshow(window_name, display_frame)
            out_writer.write(display_frame)
            frame_count += 1
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('p'):
            paused = not paused
            print("Paused" if paused else "Resumed")
    
    cap.release()
    out_writer.release()
    cv2.destroyAllWindows()
    
    total_time = time.time() - start_time
    print(f"\nProcessing complete:")
    print(f"Total frames: {frame_count}")
    print(f"Total violations detected: {total_violations}")
    print(f"Processing time: {total_time:.2f}s")
    print(f"Average FPS: {frame_count/total_time:.2f}")
    print(f"Annotated video saved to: {output_path}")

def draw_flag_on_frame_v2(frame, hand_states):
    # Draw the 4 flags for all hands, clearly visible and easy to monitor
    h, w = frame.shape[:2]
    x = 40  # Move to left side for visibility
    y_start = 80  # Start below the violation count
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    thickness = 3
    color_outline = (0, 0, 0)
    color_fill = (255, 255, 0)  # Bright yellow for visibility
    bg_color = (0, 0, 0)
    pad = 10
    line_height = 50
    for i, (hid, state) in enumerate(hand_states.items()):
        flag_text = f"{hid}:"\
            f" entered_with_scooper={state['entered_with_scooper']}"\
            f" leaves_with_scooper={state['leaves_with_scooper']}"\
            f" scooper_in_roi={state['scooper_in_roi']}"\
            f" hand_in_roi={state['hand_in_roi']}"
        y = y_start + i * line_height
        (text_w, text_h), _ = cv2.getTextSize(flag_text, font, font_scale, thickness)
        cv2.rectangle(frame, (x - pad, y - text_h - pad), (x + text_w + pad, y + pad), bg_color, -1)
        cv2.putText(frame, flag_text, (x, y), font, font_scale, color_outline, thickness + 2, cv2.LINE_AA)
        cv2.putText(frame, flag_text, (x, y), font, font_scale, color_fill, thickness, cv2.LINE_AA)
    return frame

def main():
    print("Real-Time Violation Display for Pizza Scooper Violation Detection")
    print("=" * 70)
    print("This demonstrates the production workflow with ROI overlays and violation counts.")
    print("=" * 70)
    
    videos = [
        "data/videos/Sah w b3dha ghalt (2).mp4",
        "data/videos/Sah w b3dha ghalt (3).mp4",
        
        "data/videos/Sah w b3dha ghalt.mp4"
        
    ]
    
    for i, video_path in enumerate(videos, 1):
        if os.path.exists(video_path):
            print(f"\n🎬 VIDEO {i}/3: {os.path.basename(video_path)}")
            print("=" * 50)
            
            response = input("Run real-time display for this video? (y/n): ").lower().strip()
            if response == 'y':
                run_realtime_display(video_path)
                break
        else:
            print(f"❌ Video not found: {video_path}")
    
    print("\n" + "=" * 70)
    print("Real-time display complete!")

if __name__ == "__main__":
    main() 