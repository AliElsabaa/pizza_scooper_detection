import torch
import cv2

print("🔥 Script started")

print("📦 Loading model...")
model = torch.load("model/yolo12m-v2.pt", map_location="cpu", weights_only=False)
print("✅ Model loaded")

cap = cv2.VideoCapture("data\videos\Sah b3dha ghalt.mp4")
if not cap.isOpened():
    print("Error: Could not open video source.")
    exit()

print("🎥 Starting video loop")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
