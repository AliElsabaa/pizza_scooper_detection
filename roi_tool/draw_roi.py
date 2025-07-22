"""
ROI Drawing Tool
Allows user to draw ROIs on a video frame and saves them as JSON.
"""

import cv2
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
VIDEO_PATH = os.path.join(DATA_DIR, 'videos', 'Sah b3dha ghalt.mp4')  # Change as needed
ROI_SAVE_PATH = os.path.join(DATA_DIR, 'rois', 'rois.json')


def draw_rois(frame):
    rois = []
    clone = frame.copy()
    roi = []
    drawing = [False]

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            roi.clear()
            roi.extend([x, y])
            drawing[0] = True
        elif event == cv2.EVENT_LBUTTONUP:
            roi.extend([x, y])
            drawing[0] = False
            rois.append(tuple(roi))
            cv2.rectangle(frame, (roi[0], roi[1]), (roi[2], roi[3]), (0, 255, 0), 2)

    cv2.namedWindow("Draw ROIs (drag mouse)")
    cv2.setMouseCallback("Draw ROIs (drag mouse)", mouse_callback)

    while True:
        temp = frame.copy()
        if drawing[0] and len(roi) == 2:
            cv2.rectangle(temp, (roi[0], roi[1]), (cv2.getWindowImageRect("Draw ROIs (drag mouse)")[2], cv2.getWindowImageRect("Draw ROIs (drag mouse)")[3]), (255, 0, 0), 1)
        cv2.imshow("Draw ROIs (drag mouse)", temp)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            frame[:] = clone.copy()
            rois.clear()

    cv2.destroyAllWindows()
    return rois


def main():
    if not os.path.exists(VIDEO_PATH):
        print(f"Video not found: {VIDEO_PATH}")
        return
    cap = cv2.VideoCapture(VIDEO_PATH)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Failed to read frame from video.")
        return
    print("Draw ROIs with mouse. Press 'q' to finish, 'r' to reset.")
    rois = draw_rois(frame)
    os.makedirs(os.path.dirname(ROI_SAVE_PATH), exist_ok=True)
    with open(ROI_SAVE_PATH, 'w') as f:
        json.dump([{'x1': r[0], 'y1': r[1], 'x2': r[2], 'y2': r[3]} for r in rois], f, indent=2)
    print(f"Saved {len(rois)} ROIs to {ROI_SAVE_PATH}")

if __name__ == "__main__":
    main()
