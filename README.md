# 🍕 Pizza Store Scooper Violation Detection

A microservices-based computer vision system that monitors pizza store hygiene compliance 
in real time — detecting whether workers use a scooper when picking up ingredients from 
designated regions of interest (ROIs).

---

## 🎯 Project Goal

Automate hygiene protocol enforcement in a pizza store environment by detecting violations 
— specifically when a worker's bare hand enters a monitored ingredient zone without using 
a scooper. The system processes video footage, runs object detection, and flags violations 
with bounding boxes and a running count.

---

## 🏗️ Architecture

The system follows a **microservices architecture** with each service handling a specific 
responsibility:

| Service | Responsibility |
|---------|---------------|
| `frame_reader` | Reads video files frame by frame and publishes frames to Kafka |
| `detection_service` | Runs YOLO object detection and applies violation logic per frame |
| `streaming_service` | Aggregates results and serves the video stream + detection data via REST API |
| `frontend` | Streamlit web UI — displays the live video stream, ROIs, bounding boxes, and violation count |
| `roi_tool` | Interactive tool to draw and save regions of interest on video frames |
| `shared` | Common data schemas shared across services |
| `Kafka` | Message broker that connects the frame reader to the detection pipeline |

---

## 🔍 How It Works

1. **ROI Definition** — Use the ROI tool to draw regions (e.g., ingredient containers) on a reference frame. ROIs are saved as JSON.
2. **Frame Ingestion** — The frame reader service reads video files and publishes encoded frames to a Kafka topic.
3. **Object Detection** — The detection service consumes frames from Kafka, runs YOLOv12 Medium to detect `hand`, `scooper`, `person`, and `pizza`, then checks whether a hand is inside an ROI without a scooper present.
4. **Violation Logic** — A violation is recorded when a bare hand enters a monitored ROI (no scooper detected in the same zone).
5. **Streaming & Display** — The streaming service exposes the processed video via MJPEG, and the frontend displays it in real time alongside the violation count.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Object Detection | YOLOv12 Medium (custom-trained for pizza store objects) |
| Video Processing | OpenCV |
| Message Broker | Apache Kafka + Zookeeper |
| Backend Services | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Containerization | Docker + Docker Compose |
| ML Framework | PyTorch + Ultralytics |

---

## 📁 Project Structure

pizza_scooper_detection/

│

├── frame_reader/          # Video ingestion service

├── detection_service/     # YOLO detection + violation logic

├── streaming_service/     # REST API + MJPEG video stream

├── frontend/              # Streamlit web UI

├── roi_tool/              # Interactive ROI drawing tool

├── shared/                # Common data schemas

├── data/

│   ├── videos/            # Input video files

│   └── rois/

│       └── rois.json      # Saved ROI configurations

├── model/

│   └── yolo12m-v2.pt      # Pre-trained YOLO model

├── docker-compose.yml

└── README.md

---

## ⚙️ Setup & Usage

### 1. Define Regions of Interest
Run the ROI tool on your video to draw and save the ingredient zones:
```bash
python roi_tool/draw_roi.py
```
This generates `data/rois/rois.json`. You can re-run this at any time to update ROIs.

### 2. Run the System
```bash
docker-compose up --build
```
This starts all services: Kafka, Zookeeper, frame reader, detection, streaming, and frontend.

---

## ✅ Detection Targets

The YOLO model was trained to detect the following objects in a pizza store environment:

- 🖐️ `hand`
- 🥄 `scooper`
- 🧑 `person`
- 🍕 `pizza`

---

## 📊 Test Results

Violation detection was validated on three test videos:

| Video | Expected Violations |
|-------|-------------------|
| `Sah b3dha ghalt.mp4` | 1 |
| `Sah w b3dha ghalt (2).mp4` | 2 |
| `Sah w b3dha ghalt (3).mp4` | 1 |

---

## 🔧 Troubleshooting

- If a service fails to start: `docker-compose logs [service_name]`
- Ensure video files are placed in `data/videos/`
- ROI coordinates must match the dimensions of the input video
- Model file `model/yolo12m-v2.pt` must be present (~39MB)
