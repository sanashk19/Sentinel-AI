import cv2
import numpy as np
import re
import datetime
import torch

# Fix PyTorch 2.6+ weights_only security - patch torch.load
_original_torch_load = torch.load

def _patched_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)

torch.load = _patched_load

from ultralytics import YOLO

# load pretrained field detector
model = YOLO("models/model.pt")

# Try to import OCR libraries - handle all import errors gracefully
ocr_backend = None
easyocr_reader = None

try:
    import easyocr
    easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    ocr_backend = "easyocr"
    print("OCR: Using EasyOCR backend")
except Exception as e:
    print(f"EasyOCR not available: {type(e).__name__}")

if ocr_backend is None:
    try:
        import pytesseract
        # Check if tesseract is actually available
        pytesseract.get_tesseract_version()
        ocr_backend = "tesseract"
        print("OCR: Using Tesseract backend")
    except Exception:
        print("OCR: No OCR backend available - field text extraction disabled")


def validate_aadhaar(text):
    """Validate Aadhaar number format from extracted text."""
    digits = re.sub(r'[^0-9]', '', text or "")
    if len(digits) != 12:
        return False
    if digits[0] not in '23456789':
        return False
    return True


def validate_name(text):
    """Validate name field - should be more than 3 characters."""
    if not text:
        return False
    text = text.strip()
    return len(text) > 3


def validate_gender(text):
    """Validate gender field - must be male/female/m/f."""
    text_lower = (text or "").lower().strip()
    return text_lower in ["male", "female", "m", "f"]


def validate_dob(text):
    """Validate date of birth field with proper date parsing."""
    if not text:
        return False
    
    text = text.strip()
    
    # Try multiple date formats
    date_formats = [
        "%Y-%m-%d",      # 1995-06-17
        "%d-%m-%Y",      # 17-06-1995
        "%d/%m/%Y",      # 17/06/1995
        "%Y/%m/%d",      # 1995/06/17
        "%d %b %Y",      # 17 Jun 1995
        "%d %B %Y",      # 17 June 1995
    ]
    
    for fmt in date_formats:
        try:
            date = datetime.datetime.strptime(text, fmt)
            # Reject unrealistic years
            current_year = datetime.datetime.now().year
            if date.year < 1900 or date.year > current_year:
                return False
            return True
        except ValueError:
            continue
    
    return False


def extract_text_from_crop(image_crop):
    """Extract text from image crop using available OCR backend."""
    if image_crop is None or image_crop.size == 0:
        return ""
    
    try:
        if ocr_backend == "easyocr":
            results = easyocr_reader.readtext(image_crop)
            text = " ".join([r[1] for r in results if r[2] > 0.3])
            return text.strip()
        
        elif ocr_backend == "tesseract":
            import pytesseract
            gray = cv2.cvtColor(image_crop, cv2.COLOR_BGR2GRAY)
            # Apply thresholding for better OCR
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text = pytesseract.image_to_string(thresh)
            return text.strip()
        
        else:
            # No OCR available - return placeholder
            return "[OCR_NOT_AVAILABLE]"
    
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""


def detect_fields(image_path):
    """Detect fields using YOLO model."""
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


def validate_field(label, text):
    """Validate a field based on its label."""
    validators = {
        "AADHAR_NUMBER": validate_aadhaar,
        "NAME": validate_name,
        "GENDER": validate_gender,
        "DATE_OF_BIRTH": validate_dob,
    }
    
    validator = validators.get(label)
    if validator:
        return validator(text)
    return False


def validate_document_fields(image_path):
    """
    Validate all detected fields in a document.
    
    Returns:
        tuple: (score, results) where score is 0-100 and results is a list of field details
    """
    fields = detect_fields(image_path)
    
    if not fields:
        return 0, []
    
    validation_score = 0
    results = []
    
    for field in fields:
        text = extract_text_from_crop(field["crop"])
        valid = validate_field(field["label"], text)
        
        results.append({
            "field": field["label"],
            "text": text,
            "valid": valid,
            "confidence": field["confidence"]
        })
        
        if valid:
            validation_score += 1
    
    score = (validation_score / len(fields)) * 100
    return score, results


def get_field_validation_score(image_path):
    """
    Get a single validation score for the document.
    This can be integrated into the main scoring pipeline.
    
    Returns:
        float: Validation score 0-100
    """
    score, _ = validate_document_fields(image_path)
    return score