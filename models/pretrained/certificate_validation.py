from models.pretrained.certificate_detector import detect_certificate
import cv2
import numpy as np

# OCR backend for text extraction - initialize lazily
_ocr_backend = None
_easyocr_reader = None


def _init_ocr():
    """Initialize OCR backend lazily."""
    global _ocr_backend, _easyocr_reader
    
    if _ocr_backend is not None:
        return _ocr_backend
    
    try:
        import easyocr
        _easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        _ocr_backend = "easyocr"
        print("Certificate Validation: EasyOCR initialized")
        return _ocr_backend
    except Exception as e:
        print(f"Certificate Validation: EasyOCR not available - {e}")
    
    _ocr_backend = "none"
    return _ocr_backend


def extract_text_from_image(image_path):
    """Extract text from image using OCR."""
    _init_ocr()
    
    try:
        image = cv2.imread(image_path)
        if image is None:
            return ""
        
        if _ocr_backend == "easyocr" and _easyocr_reader is not None:
            results = _easyocr_reader.readtext(image)
            text = " ".join([r[1] for r in results if r[2] > 0.1])
            return text.strip()
        else:
            # Try pytesseract
            try:
                import pytesseract
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                return pytesseract.image_to_string(thresh).strip()
            except:
                return ""
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""


def verify_certificate(image_path):
    """
    Verify certificate by detecting fields using Roboflow API or text-based fallback.
    
    Returns:
        tuple: (score, results) where score is 0-100 and results is a list of field details
    """
    # Extract OCR text for fallback detection
    ocr_text = extract_text_from_image(image_path)
    print(f"Certificate Validation: OCR extracted {len(ocr_text)} characters")
    
    try:
        detections = detect_certificate(image_path, ocr_text)
    except Exception as e:
        print(f"Certificate Detection Error: {e}")
        # Use text-based fallback
        from models.pretrained.certificate_detector import _text_based_detection
        detections = _text_based_detection(ocr_text) if ocr_text else []
    
    if not detections:
        return 0, [{"field": "CERTIFICATE", "text": "No detections", "valid": False, "confidence": 0}]
    
    total = len(detections)
    valid = 0
    results = []
    
    for d in detections:
        # Roboflow returns 'class' or 'class_name' depending on version
        label = d.get("class") or d.get("class_name") or d.get("label", "unknown")
        confidence = d.get("confidence", 0) or d.get("score", 0)
        text = d.get("text", "")
        
        # Normalize confidence to 0-1 range if needed
        if confidence > 1:
            confidence = confidence / 100
        
        results.append({
            "field": label,
            "text": text,
            "valid": confidence > 0.6,
            "confidence": confidence
        })
        
        if confidence > 0.6:
            valid += 1
    
    
    score = (valid / total) * 100 if total > 0 else 0
    return score, results