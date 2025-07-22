# Pizza Scooper Violation Detection - Testing Guide

## Overview
This guide provides step-by-step instructions to test your Pizza Scooper Violation Detection system and verify it meets all task requirements before Docker deployment.

## Prerequisites
- Python 3.8+ installed
- All project files in place
- Test videos available in `data/videos/`
- YOLO model available in `model/`

## Quick Start
Run the comprehensive test suite:
```bash
python test_project.py
```

This will run all tests and generate a detailed report.

## Individual Tests

### 1. Requirements Check
```bash
python check_requirements.py
```
**Purpose**: Verifies all dependencies and files are available
**What it checks**:
- Python packages (torch, ultralytics, opencv, etc.)
- Required files (model, videos, ROIs, services)

### 2. YOLO Model Test
```bash
python test_model.py
```
**Purpose**: Tests the YOLO model with sample video frames
**What it checks**:
- Model loading
- Object detection (hand, scooper, person, pizza)
- Detection confidence scores

### 3. ROI Configuration Test
```bash
python test_roi.py
```
**Purpose**: Tests ROI-based violation detection logic
**What it checks**:
- ROI loading and validation
- Violation detection (hand in ROI without scooper)
- Expected violation count for test video

### 4. Frame Reader Test
```bash
python test_frame_reader.py
```
**Purpose**: Tests video frame processing and encoding
**What it checks**:
- Video file reading
- Frame encoding (JPEG + base64)
- Processing performance

### 5. Streaming Service Test
```bash
python test_streaming_service.py
```
**Purpose**: Tests video overlay and streaming functionality
**What it checks**:
- ROI drawing on frames
- Detection bounding box drawing
- JPEG encoding for streaming

### 6. Frontend Test
```bash
python test_frontend.py
```
**Purpose**: Tests frontend UI components
**What it checks**:
- Streamlit UI elements
- API request functions
- Error handling

### 7. End-to-End Pipeline Test
```bash
python test_end_to_end.py
```
**Purpose**: Tests the complete pipeline without Kafka
**What it checks**:
- Full video processing workflow
- Violation detection accuracy
- System integration

## Task Requirements Verification

The test suite verifies these key requirements:

### ✅ Microservices Architecture
- **Frame Reader Service**: Video frame processing
- **Detection Service**: YOLO-based object detection
- **Streaming Service**: Real-time video streaming
- **Frontend Service**: User interface

### ✅ Core Functionality
- **Video Ingestion**: Reading from video files
- **Object Detection**: Detecting hands, scooper, person, pizza
- **ROI Monitoring**: Tracking regions of interest
- **Violation Detection**: Identifying scooper violations
- **Real-time Display**: Showing detection results

### ✅ Technical Requirements
- **YOLO 12 Medium Model**: Pre-trained for pizza store objects
- **ROI Configuration**: JSON-based region definitions
- **Base64 Encoding**: Frame transmission format
- **MJPEG Streaming**: Real-time video display
- **Violation Counting**: Total violation tracking

## Expected Results

### Test Video Violations
- `Sah b3dha ghalt.mp4`: 1 violation
- `Sah w b3dha ghalt (2).mp4`: 2 violations  
- `Sah w b3dha ghalt (3).mp4`: 1 violation

### Performance Metrics
- Frame processing: ~30 FPS
- Detection accuracy: >80% for hands and scooper
- Violation detection: Correct identification of bare hand usage

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install torch torchvision ultralytics opencv-python numpy matplotlib tqdm Pillow kafka-python fastapi uvicorn streamlit requests
   ```

2. **Model Loading Issues**
   - Ensure `model/yolo12m-v2.pt` exists (39MB file)
   - Check CUDA/CPU compatibility

3. **Video File Issues**
   - Ensure test videos are in `data/videos/`
   - Check video format compatibility

4. **ROI Configuration Issues**
   - Verify `data/rois/rois.json` format
   - Check ROI coordinates match video dimensions

### Test Failures

If tests fail:
1. Check the detailed error messages
2. Verify all prerequisites are met
3. Run individual tests to isolate issues
4. Check the generated test report

## Next Steps

After successful testing:

1. **Docker Deployment** (Optional)
   ```bash
   docker-compose up
   ```

2. **Production Deployment**
   - Set up Kafka/RabbitMQ infrastructure
   - Configure production video sources
   - Deploy services to production environment

3. **Performance Optimization**
   - GPU acceleration for detection
   - Load balancing for multiple cameras
   - Database integration for violation logging

## Report Generation

The test suite generates:
- Console output with detailed results
- `test_report_YYYYMMDD_HHMMSS.txt` file
- Individual test logs

Use these reports to:
- Verify system functionality
- Document test results
- Identify areas for improvement
- Prepare for deployment

## Support

If you encounter issues:
1. Check the test output for specific error messages
2. Verify all files and dependencies are in place
3. Run individual tests to isolate problems
4. Review the project documentation

---

**Note**: This testing approach verifies your system works without Docker, ensuring the core functionality is solid before containerization. 