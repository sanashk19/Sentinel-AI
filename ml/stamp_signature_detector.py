#!/usr/bin/env python3

from __future__ import annotations

import torch

# Patch torch.load for PyTorch 2.6+ compatibility with Ultralytics checkpoints
_original_torch_load = torch.load


def _patched_load(*args, **kwargs):
    kwargs["weights_only"] = False
    return _original_torch_load(*args, **kwargs)


torch.load = _patched_load

from pathlib import Path


CLASS_ID_TO_LABEL = {
    0: "signature",
    1: "stamp",
}


def detect_stamp_signature(image_path: str, conf: float = 0.25) -> dict:
    model_path = Path(__file__).resolve().parents[1] / "models" / "stamp_signature.pt"

    try:
        from ultralytics import YOLO
    except ImportError:
        return {
            "signature_detected": False,
            "stamp_detected": False,
            "detection_count": 0,
            "detections": [],
            "error": "ultralytics not installed",
        }

    if not model_path.exists():
        return {
            "signature_detected": False,
            "stamp_detected": False,
            "detection_count": 0,
            "detections": [],
            "error": f"model not found: {model_path}",
        }

    try:
        model = YOLO(str(model_path))
        results = model.predict(source=image_path, conf=conf, verbose=False)

        detections = []
        signature_detected = False
        stamp_detected = False

        for r in results or []:
            boxes = getattr(r, "boxes", None)
            if boxes is None:
                continue

            xyxy = getattr(boxes, "xyxy", None)
            cls = getattr(boxes, "cls", None)
            confs = getattr(boxes, "conf", None)
            if xyxy is None or cls is None or confs is None:
                continue

            for i in range(len(xyxy)):
                class_id = int(cls[i].item())
                label = CLASS_ID_TO_LABEL.get(class_id, str(class_id))
                confidence = float(confs[i].item())
                x1, y1, x2, y2 = [float(v.item()) for v in xyxy[i]]

                if label == "signature":
                    signature_detected = True
                if label == "stamp":
                    stamp_detected = True

                detections.append(
                    {
                        "label": label,
                        "confidence": confidence,
                        "bbox": [x1, y1, x2, y2],
                    }
                )

        return {
            "signature_detected": signature_detected,
            "stamp_detected": stamp_detected,
            "detection_count": len(detections),
            "detections": detections,
        }

    except Exception as e:
        return {
            "signature_detected": False,
            "stamp_detected": False,
            "detection_count": 0,
            "detections": [],
            "error": str(e),
        }
