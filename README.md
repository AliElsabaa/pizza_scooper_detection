# Pizza Store Scooper Violation Detection

## Overview
A microservices-based computer vision system to detect hygiene protocol violations in a pizza store (detects if workers use a scooper to pick up ingredients from ROIs).

## Architecture
- **frame_reader:** Reads video frames and sends them to Kafka.
- **detection_service:** Runs object detection and violation logic.
- **streaming_service:** Serves detection results and video stream to the frontend.
- **frontend:** Displays video, bounding boxes, ROIs, and violation count.
- **roi_tool:** Tool to draw and save ROIs.
- **Kafka:** Message broker for inter-service communication.

## Setup Instructions
1. Clone the repo and set up your Python virtual environment (optional).
2. Use the ROI tool to define and save ROIs:
   ```bash
   python roi_tool/draw_roi.py
   ```
3. Build and start all services with Docker Compose:
   ```bash
   docker-compose up --build
   ```
4. Access the frontend at [http://localhost:8501](http://localhost:8501)

## Usage
- The system will display the video stream, highlight detected objects, ROIs, and violations in real time.
- Violation count is shown on the frontend.

## File Structure
- `frame_reader/` - Video ingestion service
- `detection_service/` - Detection and violation logic
- `streaming_service/` - API and video streaming
- `frontend/` - Web UI
- `roi_tool/` - ROI selection tool
- `shared/` - Shared data schemas
- `data/` - Videos, ROIs, etc.
- `model/` - Pretrained YOLO model

## Notes
- You can re-run the ROI tool at any time to update ROIs.
- Make sure Kafka and Zookeeper are running (handled by Docker Compose).

## Current Status
✅ **Completed:**
- Complete microservices architecture implemented
- Docker Compose configuration with all services
- ROI tool for defining regions of interest
- YOLO model integration with ultralytics
- Frame reader service with Kafka integration
- Detection service with violation logic
- Streaming service with REST API and video stream
- Frontend UI with Streamlit
- All Dockerfiles created

## Next Steps
1. **Test the system:**
   ```bash
   docker-compose up --build
   ```
2. **Access the frontend:** http://localhost:8501
3. **Monitor logs** for any issues
4. **Record demo video** showing the system working

## Troubleshooting
- If services fail to start, check Docker logs: `docker-compose logs [service_name]`
- Ensure all video files are in `data/videos/` directory
- ROIs are already defined in `data/rois/rois.json` 