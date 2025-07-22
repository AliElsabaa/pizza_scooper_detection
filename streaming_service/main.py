"""
Streaming Service
Serves detection results and video stream to the frontend.
"""

from fastapi import FastAPI, Response
from kafka import KafkaConsumer
import threading
import json
import cv2
import base64
import numpy as np
import time
import os

KAFKA_TOPIC = "detections"
KAFKA_SERVER = "kafka:29092"  # Use Docker service name and internal port
ROI_PATH = os.path.join("data", "rois", "rois.json")

app = FastAPI()

# Store latest detection results and frames
latest_results = {}
latest_violations = []
rois = []

# Load ROIs at startup
def load_rois():
    global rois
    with open(ROI_PATH, 'r') as f:
        rois = json.load(f)

# Helper to draw overlays on frame
def draw_overlays(frame, detections, violations):
    # Draw ROIs
    for idx, roi in enumerate(rois):
        color = (0, 255, 0)
        if any(v['roi_id'] == idx for v in violations):
            color = (0, 0, 255)  # Red for violation
        cv2.rectangle(frame, (roi['x1'], roi['y1']), (roi['x2'], roi['y2']), color, 2)
    # Draw detections
    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        label = det['label']
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
        cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 2)
    return frame

# Helper to decode base64 image to numpy array
def decode_image(image_b64):
    jpg_original = base64.b64decode(image_b64)
    jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
    img = cv2.imdecode(jpg_as_np, flags=1)
    return img

# Helper to encode frame as JPEG bytes
def encode_jpeg(frame):
    ret, buffer = cv2.imencode('.jpg', frame)
    return buffer.tobytes() if ret else None

# Kafka consumer loop (runs in background)
def consume_detections():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_SERVER,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id='streaming-service'
    )
    for msg in consumer:
        data = msg.value
        latest_results[data['frame_id']] = data
        if data['violations']:
            latest_violations.extend(data['violations'])

@app.on_event("startup")
def startup_event():
    load_rois()
    threading.Thread(target=consume_detections, daemon=True).start()

@app.get("/metadata")
def get_metadata():
    # Return number of violations (placeholder)
    return {"violations": len(latest_violations)}

@app.get("/video-stream")
def video_stream():
    def gen():
        last_frame_id = -1
        while True:
            # Get the latest frame with detections
            if not latest_results:
                time.sleep(0.05)
                continue
            frame_id = max(latest_results.keys())
            if frame_id == last_frame_id:
                time.sleep(0.03)
                continue
            last_frame_id = frame_id
            data = latest_results[frame_id]
            frame = decode_image(data.get('image', '')) if 'image' in data else None
            if frame is None:
                continue
            frame = draw_overlays(frame, data.get('detections', []), data.get('violations', []))
            jpeg = encode_jpeg(frame)
            if jpeg is not None:
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n')
            time.sleep(0.03)
    return Response(gen(), media_type='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
