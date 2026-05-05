from ultralytics import YOLO

model = YOLO("aadhar_yolov8.pt")

def detect_aadhar(image_path):

    results = model(image_path)

    boxes = results[0].boxes

    if len(boxes) == 0:
        return {"detected": False}

    return {
        "detected": True,
        "confidence": float(boxes.conf.mean())
    }