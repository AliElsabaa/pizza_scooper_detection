"""
Frontend UI
Displays video stream, bounding boxes, ROIs, and violation count.
"""

import streamlit as st
import requests
from PIL import Image
import io
import time

BACKEND_URL = "http://streaming_service:8000"  # Use Docker service name

st.title("Pizza Store Scooper Violation Detection")

# Display violation count
violation_placeholder = st.empty()

# Display video stream
frame_placeholder = st.empty()

# Function to fetch violation count
def get_violation_count():
    try:
        resp = requests.get(f"{BACKEND_URL}/metadata")
        if resp.status_code == 200:
            return resp.json().get("violations", 0)
    except Exception:
        return "N/A"
    return "N/A"

# Function to fetch video stream (MJPEG)
def video_stream():
    try:
        resp = requests.get(f"{BACKEND_URL}/video-stream", stream=True)
        bytes_data = b""
        for chunk in resp.iter_content(chunk_size=1024):
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8')
            b_ = bytes_data.find(b'\xff\xd9')
            if a != -1 and b_ != -1:
                jpg = bytes_data[a:b_+2]
                bytes_data = bytes_data[b_+2:]
                img = Image.open(io.BytesIO(jpg))
                frame_placeholder.image(img, channels="BGR")
                break
    except Exception:
        pass

# Main loop
def main_loop():
    while True:
        violation_count = get_violation_count()
        violation_placeholder.markdown(f"**Violation count:** {violation_count}")
        video_stream()
        time.sleep(0.1)

main_loop()
