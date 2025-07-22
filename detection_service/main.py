"""
Detection Service
Subscribes to the message broker, runs object detection, and checks for violations
using refined temporal logic for hands, scooper, and pizza.
"""

from kafka import KafkaConsumer, KafkaProducer
import json
from ultralytics import YOLO
import cv2
import base64
import numpy as np
import os

KAFKA_TOPIC_IN = "frames"
KAFKA_TOPIC_OUT = "detections"
KAFKA_SERVER = "kafka:29092"  # Use Docker service name and internal port
MODEL_PATH = os.path.join("model", "yolo12m-v2.pt")
ROI_PATH = os.path.join("data", "rois", "rois.json")

# ----------------- Utility Functions -----------------

def decode_image(image_b64):
    jpg_original = base64.b64decode(image_b64)
    jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
    img = cv2.imdecode(jpg_as_np, flags=1)
    return img

def iou(box1, box2):
    """IoU between two [x1, y1, x2, y2] boxes"""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    box1_area = (box1[2]-box1[0]) * (box1[3]-box1[1])
    box2_area = (box2[2]-box2[0]) * (box2[3]-box2[1])
    union_area = box1_area + box2_area - inter_area
    return inter_area / union_area if union_area > 0 else 0

# ----------------- Violation Tracking State -----------------
GRACE_FRAMES = 10        # Drop old hands after not seen for ~1 sec (10fps)
WAIT_AFTER_LEAVE = 5     # Wait 5 frames after leaving ROI
CONF_SCOOPER = 0.3       # Lower threshold for scooper
CONF_HAND = 0.5
CONF_PIZZA = 0.5

hand_states = {}  # hand_id -> tracking state

# ----------------- Main Service -----------------

def main():
    consumer = KafkaConsumer(
        KAFKA_TOPIC_IN,
        bootstrap_servers=KAFKA_SERVER,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id='detection-service'
    )
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_SERVER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    print("Loading YOLO model...")
    model = YOLO(MODEL_PATH)
    print("Model loaded.")

    with open(ROI_PATH, 'r') as f:
        rois = json.load(f)
    print(f"Loaded {len(rois)} ROIs.")

    # We’ll cache all frame results for temporal checks
    frames_results = []

    for msg in consumer:
        frame_data = msg.value
        frame_id = frame_data["frame_id"]
        image = decode_image(frame_data["image"])

        results = model(image)
        detections = []
        hands, scoopers, pizzas = [], [], []

        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    xyxy = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())
                    cls = int(box.cls[0].cpu().numpy())
                    label = result.names[cls]
                    bbox = [int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])]
                    detections.append({"label": label, "bbox": bbox, "score": conf})

                    if label.lower() == "hand" and conf > CONF_HAND:
                        hands.append({"bbox": bbox, "conf": conf})
                    elif label.lower() == "scooper" and conf > CONF_SCOOPER:
                        scoopers.append({"bbox": bbox, "conf": conf})
                    elif label.lower() == "pizza" and conf > CONF_PIZZA:
                        pizzas.append({"bbox": bbox, "conf": conf})

        # Store per-frame results for post-processing
        frames_results.append({
            "frame_id": frame_id,
            "hands": hands,
            "scoopers": scoopers,
            "pizzas": pizzas
        })

        # ----------------- Violation Logic -----------------
        violations = []

        for idx, hand in enumerate(hands):
            hand_id = f"hand_{idx}"
            state = hand_states.get(hand_id, {
                "in_roi": False,
                "roi_exit_frame": None,
                "decision_pending": False,
                "decision_window_start": None,
                "violation_raised": False,
                "no_violation": False,
                "last_seen_frame": frame_id
            })
            state["last_seen_frame"] = frame_id

            # Check if hand is inside any ROI
            hand_roi_iou = max(iou(hand["bbox"], [r["x1"], r["y1"], r["x2"], r["y2"]]) for r in rois)

            if hand_roi_iou > 0:
                if not state["in_roi"]:
                    # Just entered ROI
                    state.update({
                        "in_roi": True,
                        "roi_exit_frame": None,
                        "decision_pending": False,
                        "violation_raised": False,
                        "no_violation": False
                    })
            else:
                if state["in_roi"]:
                    # Hand just left ROI
                    state["in_roi"] = False
                    state["roi_exit_frame"] = frame_id
                    state["decision_pending"] = True
                    state["decision_window_start"] = frame_id + WAIT_AFTER_LEAVE

            # Evaluate decision window
            if state["decision_pending"] and not state["violation_raised"] and not state["no_violation"]:
                if frame_id >= (state["decision_window_start"] or 0):
                    # Look ahead from current frame to end of buffer
                    look_idx = len(frames_results) - 1
                    scooper_seen_with_pizza = False

                    while look_idx < len(frames_results):
                        frame_info = frames_results[look_idx]
                        hands_f = frame_info["hands"]
                        scoopers_f = frame_info["scoopers"]
                        pizzas_f = frame_info["pizzas"]

                        if idx < len(hands_f):
                            look_hand = hands_f[idx]
                            # Check hand re-enters ROI
                            if max(iou(look_hand["bbox"], [r["x1"], r["y1"], r["x2"], r["y2"]]) for r in rois) > 0:
                                # Reset
                                state["decision_pending"] = False
                                state["roi_exit_frame"] = None
                                break

                            # Check scooper with pizza
                            scooper_with_pizza = any(
                                iou(s["bbox"], p["bbox"]) > 0 for s in scoopers_f for p in pizzas_f
                            )
                            if scooper_with_pizza:
                                scooper_seen_with_pizza = True

                            # Check scooper in ROI (visible)
                            scooper_in_roi = any(
                                max(iou(s["bbox"], [r["x1"], r["y1"], r["x2"], r["y2"]]) for r in rois) > 0
                                for s in scoopers_f
                            )

                            # Check hand with pizza
                            hand_with_pizza = any(
                                iou(look_hand["bbox"], p["bbox"]) > 0 for p in pizzas_f
                            )

                            # Decision rules
                            if scooper_with_pizza:
                                state["no_violation"] = True
                                state["decision_pending"] = False
                                break

                            if (scooper_in_roi or not scooper_seen_with_pizza) and hand_with_pizza:
                                violations.append({
                                    "roi_id": 0,
                                    "type": "hand_grabbed_without_scooper"
                                })
                                state["violation_raised"] = True
                                state["decision_pending"] = False
                                break
                        look_idx += 1

            hand_states[hand_id] = state

        # Clean up old hands
        for hid in list(hand_states.keys()):
            if frame_id - hand_states[hid]["last_seen_frame"] > GRACE_FRAMES:
                del hand_states[hid]

        detection_result = {
            "frame_id": frame_id,
            "image": frame_data["image"],
            "detections": detections,
            "violations": violations
        }
        producer.send(KAFKA_TOPIC_OUT, detection_result)

    producer.close()

if __name__ == "__main__":
    main()
