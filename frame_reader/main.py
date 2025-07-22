"""
Frame Reader Service
Reads video frames from a file or RTSP stream and publishes them to the message broker.
"""

import cv2
from kafka import KafkaProducer
import json
import time
import base64

VIDEO_PATH = "data/videos/Sah b3dha ghalt.mp4"  # Change as needed
KAFKA_TOPIC = "frames"
KAFKA_SERVER = "kafka:29092"  # Use Docker service name and internal port


def encode_frame(frame):
    # Encode frame as JPEG, then base64
    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        return None
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    return jpg_as_text


def main():
    # Set up Kafka producer
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_SERVER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    # Open video file
    cap = cv2.VideoCapture(VIDEO_PATH)
    frame_id = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        encoded = encode_frame(frame)
        if encoded is None:
            continue
        frame_data = {
            "frame_id": frame_id,
            "timestamp": time.time(),
            "image": encoded
        }
        producer.send(KAFKA_TOPIC, frame_data)
        frame_id += 1
        time.sleep(0.03)  # Simulate ~30 FPS
    cap.release()
    producer.close()
    print("Frame Reader finished.")

if __name__ == "__main__":
    main()
