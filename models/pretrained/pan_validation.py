import cv2
import numpy as np
import re
import os
import torch

# Fix PyTorch 2.6+ weights_only security - patch torch.load
_original_torch_load = torch.load

def _patched_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)

torch.load = _patched_load

from ultralytics import YOLO

# Load pretrained PAN detection model
model = None
model_path = "models/pan_card_model.pt"

try:
    if os.path.exists(model_path):
        model = YOLO(model_path)
        print("PAN Model: Loaded successfully")
        print(f"PAN Model classes: {model.names}")
    else:
        print(f"PAN Model: Model file not found at {model_path}")
        print("Run 'python download_pan_model.py' to download the model")
except Exception as e:
    print(f"PAN Model: Error loading - {type(e).__name__}: {e}")

# OCR backend
ocr_backend = None
easyocr_reader = None

try:
    import easyocr
    easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    ocr_backend = "easyocr"
except Exception:
    pass


def validate_pan_format(text):
    """Validate PAN number format: ABCDE1234F"""
    if not text:
        return False, None
    
    # Normalize text - remove spaces and special chars
    normalized = re.sub(r'[^A-Z0-9]', '', text.upper())
    
    # PAN pattern: 5 letters, 4 digits, 1 letter
    pattern = r"[A-Z]{5}[0-9]{4}[A-Z]"
    match = re.search(pattern, normalized)
    
    if match:
        return True, match.group()
    
    return False, None


def extract_text_from_crop(image_crop):
    """Extract text from image crop using OCR."""
    if image_crop is None or image_crop.size == 0:
        return ""
    
    try:
        if ocr_backend == "easyocr":
            results = easyocr_reader.readtext(image_crop)
            text = " ".join([r[1] for r in results if r[2] > 0.3])
            return text.strip()
        else:
            # Fallback to basic OCR
            gray = cv2.cvtColor(image_crop, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            # Try pytesseract if available
            try:
                import pytesseract
                return pytesseract.image_to_string(thresh).strip()
            except:
                return ""
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""


def detect_pan_fields(image_path):
    """Detect PAN card fields using YOLO model."""
    if model is None:
        return []
    
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    results = model(image)
    detected_fields = []
    
    for box in results[0].boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        label = model.names[int(box.cls[0])]
        conf = float(box.conf[0])
        
        # Ensure crop coordinates are within image bounds
        h, w = image.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        crop = image[y1:y2, x1:x2]
        
        detected_fields.append({
            "label": label,
            "confidence": conf,
            "bbox": [x1, y1, x2 - x1, y2 - y1],  # [x, y, w, h] format for frontend
            "crop": crop
        })
    
    return detected_fields


def verify_pan_card(image_path):
    """
    Verify PAN card by detecting fields and validating them.
    
    Returns:
        tuple: (score, results) where score is 0-100 and results is a list of field details
    """
    if model is None:
        return 0, [{"field": "MODEL", "text": "PAN model not loaded", "valid": False, "confidence": 0}]
    
    fields = detect_pan_fields(image_path)
    
    if not fields:
        return 0, []
    
    validation_score = 0
    results = []
    
    for field in fields:
        text = extract_text_from_crop(field["crop"])
        valid = False
        
        label_lower = field["label"].lower()
        
        # Check if this field contains PAN number
        if "pan" in label_lower and "number" in label_lower:
            valid, pan_number = validate_pan_format(text)
            if valid:
                text = pan_number  # Show cleaned PAN number
        elif "name" in label_lower:
            # Name should be at least 2 characters
            valid = len(text.strip()) >= 2
        elif "dob" in label_lower or "date" in label_lower:
            # DOB should contain numbers
            valid = any(c.isdigit() for c in text)
        elif "father" in label_lower:
            # Father's name should be at least 2 characters
            valid = len(text.strip()) >= 2
        else:
            # For other detected fields, just check if text was extracted
            valid = len(text.strip()) > 0
        
        results.append({
            "field": field["label"],
            "text": text,
            "valid": valid,
            "confidence": field["confidence"]
        })
        
        if valid:
            validation_score += 1
    
    score = (validation_score / len(fields)) * 100 if fields else 0
    return score, results


def get_pan_validation_score(image_path):
    """
    Get a single validation score for the PAN card.
    
    Returns:
        float: Validation score 0-100
    """
    score, _ = verify_pan_card(image_path)
    return score