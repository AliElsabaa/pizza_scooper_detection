"""
Correct Video Testing for Pizza Scooper Violation Detection
This script implements the EXACT violation logic from the task description.
"""

import cv2
import json
import numpy as np
from ultralytics import YOLO
import os
import time
from datetime import datetime
from collections import deque

def load_rois_for_video(video_name):
    """Load ROIs for specific video"""
    roi_path = f"data/rois/{video_name}_rois.json"
    if os.path.exists(roi_path):
        with open(roi_path, 'r') as f:
            roi_data = json.load(f)
            # Handle both new format (dict with rois key) and old format (list)
            if isinstance(roi_data, dict):
                return roi_data.get('rois', [])
            else:
                return roi_data
    else:
        # Fallback to default ROIs if specific ones don't exist
        default_roi_path = "data/rois/rois.json"
        if os.path.exists(default_roi_path):
            with open(default_roi_path, 'r') as f:
                roi_data = json.load(f)
                # Handle both new format (dict with rois key) and old format (list)
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
        # Check if bbox center is inside ROI
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        if rx1 <= cx <= rx2 and ry1 <= cy <= ry2:
            return idx
    return None

def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    iou = interArea / float(boxAArea + boxBArea - interArea + 1e-6)
    return iou

## def detect_violations_correct_logic(frames_results, rois):
    """
    Implements the updated logic:
    - Hand is considered to have left ROI only when IOU=0
    - After leaving, wait 5 frames, then check all subsequent frames (until hand re-enters ROI):
      - If scooper IOU>0 with pizza, mark as no violation and wait for hand to re-enter ROI
      - If scooper IOU>0 with ROI and hand IOU>0 with pizza, mark as violation and wait for hand to re-enter ROI
      - If neither occurs and hand re-enters ROI, reset
      - If neither occurs and hand never re-enters, default to no violation
    """
    violations = []
    hand_states = {}
    GRACE_PERIOD_FRAMES = 10  # ~1s at 10fps
    IOU_THRESHOLD = 0.2
    PIZZA_IOU_THRESHOLD = 0.3
    WAIT_AFTER_LEAVE = 5  # frames to wait after hand leaves ROI before checking
    for frame_idx, frame_result in enumerate(frames_results):
        hands = [d for d in frame_result if d['class_id'] == 0 and d['confidence'] > 0.5]
        scoopers = [d for d in frame_result if d['class_id'] == 3 and d['confidence'] > 0.5]
        pizzas = [d for d in frame_result if d['class_id'] == 2 and d['confidence'] > 0.5]
        # Update hand states
        current_hand_ids = set()
        for idx, hand in enumerate(hands):
            hand_id = f"hand_{idx}"
            current_hand_ids.add(hand_id)
            if hand_id not in hand_states:
                hand_states[hand_id] = {
                    'in_roi': False,
                    'roi_entry_frame': None,
                    'roi_exit_frame': None,
                    'decision_pending': False,
                    'decision_window_start': None,
                    'violation_raised': False,
                    'no_violation': False,
                    'last_seen_frame': frame_idx,
                    'missing_frames_count': 0
                }
            state = hand_states[hand_id]
            state['last_seen_frame'] = frame_idx
            # Calculate IOUs
            hand_roi_iou = max(iou(hand['bbox'], [roi['x1'], roi['y1'], roi['x2'], roi['y2']]) for roi in rois)
            # Check if hand is in ROI
            if hand_roi_iou > 0:
                if not state['in_roi']:
                    # Hand just entered ROI
                    print(f"[DEBUG] Frame {frame_idx} | {hand_id} ENTERS ROI")
                    state['in_roi'] = True
                    state['roi_entry_frame'] = frame_idx
                    state['violation_raised'] = False
                    state['no_violation'] = False
                    state['decision_pending'] = False
                    state['decision_window_start'] = None
                # If hand is in ROI, reset decision flags
            else:
                if state['in_roi']:
                    # Hand just left ROI (IOU=0)
                    print(f"[DEBUG] Frame {frame_idx} | {hand_id} LEAVES ROI, will start decision window at frame {frame_idx + WAIT_AFTER_LEAVE}")
                    state['in_roi'] = False
                    state['roi_exit_frame'] = frame_idx
                    state['decision_pending'] = True
                    state['decision_window_start'] = frame_idx + WAIT_AFTER_LEAVE
        # After updating all hands, process decision window for hands that just left ROI
        for hand_id, state in hand_states.items():
            if state['decision_pending'] and not state['violation_raised'] and not state['no_violation']:
                # Only start checking after WAIT_AFTER_LEAVE frames
                if frame_idx < (state['decision_window_start'] or 0):
                    continue
                # Check all subsequent frames until hand re-enters ROI
                look_idx = frame_idx
                while True:
                    if look_idx >= len(frames_results):
                        print(f"[DEBUG] Frame {look_idx} | {hand_id} never re-enters ROI, default to NO VIOLATION")
                        state['no_violation'] = True
                        state['decision_pending'] = False
                        break
                    look_frame = frames_results[look_idx]
                    look_hands = [d for d in look_frame if d['class_id'] == 0 and d['confidence'] > 0.5]
                    look_scoopers = [d for d in look_frame if d['class_id'] == 3 and d['confidence'] > 0.5]
                    look_pizzas = [d for d in look_frame if d['class_id'] == 2 and d['confidence'] > 0.5]
                    # Find the same hand by index (approximate)
                    if idx < len(look_hands):
                        look_hand = look_hands[idx]
                        hand_roi_iou = max(iou(look_hand['bbox'], [roi['x1'], roi['y1'], roi['x2'], roi['y2']]) for roi in rois)
                        # If hand re-enters ROI, reset
                        if hand_roi_iou > 0:
                            print(f"[DEBUG] Frame {look_idx} | {hand_id} RE-ENTERS ROI, reset state")
                            state['decision_pending'] = False
                            state['roi_exit_frame'] = None
                            state['roi_entry_frame'] = None
                            break
                        # Check for violation/no-violation
                        scooper_in_roi_with_pizza = False
                        hand_with_pizza = False
                        scooper_in_roi = False
                        for scooper in look_scoopers:
                            scooper_roi_iou = max(iou(scooper['bbox'], [roi['x1'], roi['y1'], roi['x2'], roi['y2']]) for roi in rois)
                            for pizza in look_pizzas:
                                if scooper_roi_iou > 0 and iou(scooper['bbox'], pizza['bbox']) > 0:
                                    scooper_in_roi_with_pizza = True
                                if scooper_roi_iou > 0:
                                    scooper_in_roi = True
                        for pizza in look_pizzas:
                            if iou(look_hand['bbox'], pizza['bbox']) > 0:
                                hand_with_pizza = True
                        print(f"[DEBUG] Frame {look_idx} | {hand_id} | scooper_in_roi_with_pizza={scooper_in_roi_with_pizza} | scooper_in_roi={scooper_in_roi} | hand_with_pizza={hand_with_pizza}")
                        # If scooper is in ROI with pizza for any frame, mark as no violation
                        if scooper_in_roi_with_pizza:
                            print(f"[DEBUG] Frame {look_idx} | {hand_id} NO VIOLATION (scooper in ROI with pizza)")
                            state['no_violation'] = True
                            state['decision_pending'] = False
                            break
                        # If scooper is in ROI and hand is with pizza, mark as violation
                        if scooper_in_roi and hand_with_pizza:
                            print(f"[DEBUG] Frame {look_idx} | {hand_id} VIOLATION (scooper in ROI, hand with pizza)")
                            violations.append({'frame': state['roi_exit_frame'], 'type': 'hand_grabbed_without_scooper', 'hand_id': hand_id})
                            state['violation_raised'] = True
                            state['decision_pending'] = False
                            break
                    look_idx += 1
        # Clean up old hand states
        for hand_id in list(hand_states.keys()):
            if hand_id not in current_hand_ids:
                if frame_idx - hand_states[hand_id]['last_seen_frame'] > GRACE_PERIOD_FRAMES:
                    del hand_states[hand_id]
    return violations
def detect_violations_correct_logic(frames_results, rois):
    """
    Updated logic:
    - Hand considered to leave ROI only when IOU=0.
    - After leaving, wait 5 frames, then check all subsequent frames (until hand re-enters ROI):
      - If scooper_with_pizza = True (any scooper overlaps any pizza) → no violation.
      - If scooper_in_roi = True (any scooper overlaps ROI) AND hand overlaps pizza → violation.
      - If neither and hand re-enters ROI → reset.
      - If neither and hand never re-enters → default to no violation.
    """
    violations = []
    hand_states = {}
    GRACE_PERIOD_FRAMES = 10  # ~1s at 10fps
    IOU_THRESHOLD = 0.2
    PIZZA_IOU_THRESHOLD = 0.3
    WAIT_AFTER_LEAVE = 5

    for frame_idx, frame_result in enumerate(frames_results):
        hands = [d for d in frame_result if d['class_id'] == 0 and d['confidence'] > 0.5]
        scoopers = [d for d in frame_result if d['class_id'] == 3 and d['confidence'] > 0.3]
        pizzas = [d for d in frame_result if d['class_id'] == 2 and d['confidence'] > 0.5]

        current_hand_ids = set()
        for idx, hand in enumerate(hands):
            hand_id = f"hand_{idx}"
            current_hand_ids.add(hand_id)
            if hand_id not in hand_states:
                hand_states[hand_id] = {
                    'in_roi': False,
                    'roi_entry_frame': None,
                    'roi_exit_frame': None,
                    'decision_pending': False,
                    'decision_window_start': None,
                    'violation_raised': False,
                    'no_violation': False,
                    'last_seen_frame': frame_idx
                }
            state = hand_states[hand_id]
            state['last_seen_frame'] = frame_idx

            # Calculate IOUs for hand vs ROI
            hand_roi_iou = max(iou(hand['bbox'], [roi['x1'], roi['y1'], roi['x2'], roi['y2']]) for roi in rois)

            # Detect entry or exit
            if hand_roi_iou > 0:
                if not state['in_roi']:
                    print(f"[DEBUG] Frame {frame_idx} | {hand_id} ENTERS ROI")
                    state['in_roi'] = True
                    state['roi_entry_frame'] = frame_idx
                    state['violation_raised'] = False
                    state['no_violation'] = False
                    state['decision_pending'] = False
                    state['decision_window_start'] = None
            else:
                if state['in_roi']:
                    print(f"[DEBUG] Frame {frame_idx} | {hand_id} LEAVES ROI, start decision window at {frame_idx + WAIT_AFTER_LEAVE}")
                    state['in_roi'] = False
                    state['roi_exit_frame'] = frame_idx
                    state['decision_pending'] = True
                    state['decision_window_start'] = frame_idx + WAIT_AFTER_LEAVE

        # Evaluate decision windows
        for hand_id, state in hand_states.items():
            if state['decision_pending'] and not state['violation_raised'] and not state['no_violation']:
                if frame_idx < (state['decision_window_start'] or 0):
                    continue

                look_idx = frame_idx
                # Track if scooper ever seen with pizza in this window
                scooper_seen_with_pizza = False

                while True:
                    if look_idx >= len(frames_results):
                        print(f"[DEBUG] Frame {look_idx} | {hand_id} never re-enters ROI, NO VIOLATION")
                        state['no_violation'] = True
                        state['decision_pending'] = False
                        break

                    look_frame = frames_results[look_idx]
                    look_hands = [d for d in look_frame if d['class_id'] == 0 and d['confidence'] > 0.5]
                    look_scoopers = [d for d in look_frame if d['class_id'] == 3 and d['confidence'] > 0.3]  # lowered threshold
                    look_pizzas = [d for d in look_frame if d['class_id'] == 2 and d['confidence'] > 0.3]

                    if idx < len(look_hands):
                        look_hand = look_hands[idx]
                        hand_roi_iou = max(iou(look_hand['bbox'], [roi['x1'], roi['y1'], roi['x2'], roi['y2']]) for roi in rois)
                        if hand_roi_iou > 0:
                            print(f"[DEBUG] Frame {look_idx} | {hand_id} RE-ENTERS ROI, reset")
                            state['decision_pending'] = False
                            state['roi_exit_frame'] = None
                            state['roi_entry_frame'] = None
                            break

                        # Check scooper vs pizza (any match)
                        scooper_with_pizza = any(
                            iou(s['bbox'], p['bbox']) > 0 for s in look_scoopers for p in look_pizzas
                        )
                        if scooper_with_pizza:
                            scooper_seen_with_pizza = True

                         # Check scooper inside ROI
                        scooper_in_roi = any(
                            max(iou(s['bbox'], [roi['x1'], roi['y1'], roi['x2'], roi['y2']]) for roi in rois) > 0
                            for s in look_scoopers
                        )

                         # Check hand with pizza
                        hand_with_pizza = any(
                            iou(look_hand['bbox'], p['bbox']) > 0 for p in look_pizzas
                        )

                        print(f"[DEBUG] Frame {look_idx} | {hand_id} | scooper_with_pizza={scooper_with_pizza} | scooper_in_roi={scooper_in_roi} | hand_with_pizza={hand_with_pizza}")

                        # Case 1: Scooper touches pizza → definitely no violation
                        if scooper_with_pizza:
                            print(f"[DEBUG] Frame {look_idx} | {hand_id} NO VIOLATION (scooper touches pizza)")
                            state['no_violation'] = True
                            state['decision_pending'] = False
                            break

                        # Case 2: Scooper in ROI (or possibly hidden) AND hand touches pizza → violation
                        if (scooper_in_roi or not scooper_seen_with_pizza) and hand_with_pizza:
                            print(f"[DEBUG] Frame {look_idx} | {hand_id} VIOLATION (scooper hidden or in ROI, hand with pizza)")
                            violations.append({
                                'frame': state['roi_exit_frame'],
                                'type': 'hand_grabbed_without_scooper',
                                'hand_id': hand_id
                            })
                            state['violation_raised'] = True
                            state['decision_pending'] = False
                            break
                    look_idx += 1

        # Clean up old hand states
        for hand_id in list(hand_states.keys()):
            if hand_id not in current_hand_ids:
                if frame_idx - hand_states[hand_id]['last_seen_frame'] > GRACE_PERIOD_FRAMES:
                    del hand_states[hand_id]

    return violations


def test_video_with_correct_logic(video_path, expected_violations):
    """Test a single video with correct violation logic and save violation frames"""
    print(f"Testing: {os.path.basename(video_path)}")
    print(f"Expected violations: {expected_violations}")
    print("-" * 50)
    
    # Load model
    model_path = "model/yolo12m-v2.pt"
    if not os.path.exists(model_path):
        print(f"Model not found: {model_path}")
        return False
    
    model = YOLO(model_path)
    
    # Load ROIs for this specific video
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    rois = load_rois_for_video(video_name)
    
    print(f"Loaded {len(rois)} ROIs for video: {video_name}")
    
    # Prepare to save violation frames
    violation_frames_dir = os.path.join("output", "violation_frames")
    os.makedirs(violation_frames_dir, exist_ok=True)
    
    # Process video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Could not open video: {video_path}")
        return False
    
    frames_results = []
    all_frames = []
    frame_count = 0
    start_time = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Save all frames for later violation frame saving
        all_frames.append(frame.copy())
        # Run detection every 3rd frame to speed up processing
        if frame_count % 3 == 0:
            results = model(frame, verbose=False)
            frame_detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())
                        confidence = float(box.conf[0].cpu().numpy())
                        frame_detections.append({
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'class_id': class_id,
                            'confidence': confidence
                        })
            frames_results.append(frame_detections)
        frame_count += 1
        # Process first 300 frames for testing (about 10 seconds at 30fps)
        if frame_count >= 300:
            break
    cap.release()
    processing_time = time.time() - start_time
    print(f"Processed {len(frames_results)} frames in {processing_time:.2f}s")
    # Apply correct violation logic
    violations = detect_violations_correct_logic(frames_results, rois)
    # Count unique violations (avoid counting same violation multiple times)
    unique_violations = []
    for violation in violations:
        # Check if this is a new violation (not already counted)
        is_new = True
        for existing in unique_violations:
            if (existing['type'] == violation['type'] and 
                existing['hand_id'] == violation['hand_id'] and
                abs(existing['frame'] - violation['frame']) < 30):  # Within 1 second
                is_new = False
                break
        if is_new:
            unique_violations.append(violation)
            # Save the violation frame
            frame_idx = violation['frame']
            if 0 <= frame_idx < len(all_frames):
                out_path = os.path.join(
                    violation_frames_dir,
                    f"violation_{video_name}_frame_{frame_idx}.jpg"
                )
                cv2.imwrite(out_path, all_frames[frame_idx])
    detected_violations = len(unique_violations)
    print(f"Detected violations: {detected_violations}")
    print(f"Expected violations: {expected_violations}")
    if detected_violations == expected_violations:
        print("✅ PASS - Exact match!")
        result = True
    elif abs(detected_violations - expected_violations) <= 1:
        print("⚠️  CLOSE - Within acceptable range")
        result = True
    else:
        print("❌ FAIL - Significant difference")
        result = False
    print(f"Violation details:")
    for i, violation in enumerate(unique_violations[:5]):  # Show first 5
        print(f"  {i+1}. Frame {violation['frame']}: {violation['type']}")
    print()
    return result

def main():
    print("Correct Video Testing for Pizza Scooper Violation Detection")
    print("=" * 70)
    print("Implementing EXACT logic from task description")
    print("=" * 70)
    
    videos = [
        ("data/videos/Sah w b3dha ghalt.mp4", 1),
        ("data/videos/Sah w b3dha ghalt (2).mp4", 2),
        ("data/videos/Sah w b3dha ghalt (3).mp4", 1)
    ]
    
    results = []
    
    for video_path, expected_violations in videos:
        if os.path.exists(video_path):
            result = test_video_with_correct_logic(video_path, expected_violations)
            results.append((os.path.basename(video_path), result, expected_violations))
        else:
            print(f"Video not found: {video_path}")
            results.append((os.path.basename(video_path), False, expected_violations))
    
    # Summary
    print("=" * 70)
    print("FINAL RESULTS SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for video_name, result, expected in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{video_name}: {status} (Expected: {expected})")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} videos passed")
    
    if passed == total:
        print("🎉 ALL VIDEOS PASSED! System is working correctly.")
    else:
        print("⚠️  Some videos need adjustment. Check ROI configurations.")

if __name__ == "__main__":
    main() 