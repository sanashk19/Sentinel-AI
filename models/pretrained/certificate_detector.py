#!/usr/bin/env python3
"""
Certificate Detector - Detects certificate fields using Roboflow API
"""

# Try to import inference SDK
CLIENT = None
try:
    from inference_sdk import InferenceHTTPClient
    CLIENT = InferenceHTTPClient(
        api_url="https://serverless.roboflow.com",
        api_key="NimZhDIdNBZ4NLFACkku"
    )
    print("Certificate Detector: Roboflow API client initialized")
except ImportError:
    print("Certificate Detector: inference-sdk not installed. Run: pip install inference-sdk")
except Exception as e:
    print(f"Certificate Detector: Error initializing - {e}")


def detect_certificate(image_path, ocr_text=None):
    """
    Detect certificate fields using Roboflow API.
    
    Args:
        image_path (str): Path to the image file
        ocr_text (str, optional): OCR text for fallback detection
        
    Returns:
        list: List of detections with class and confidence
    """
    # Try Roboflow API first
    if CLIENT is not None:
        try:
            result = CLIENT.infer(image_path, model_id="certificates-zbdhx/1")
            detections = result.get("predictions", [])
            if detections:
                return detections
        except Exception as e:
            print(f"Roboflow API Error: {e}")
    
    # Fallback: text-based certificate detection
    if ocr_text:
        return _text_based_detection(ocr_text)
    
    # No OCR text available - return empty
    print("Certificate Detector: No OCR text available for fallback detection")
    return []


def _text_based_detection(text):
    """Fallback text-based certificate detection."""
    import re
    
    text_lower = text.lower()
    detections = []
    
    # Certificate keywords
    certificate_keywords = [
        'certificate', 'certify', 'certified', 'awarded', 'degree',
        'diploma', 'graduation', 'bachelor', 'master', 'doctorate',
        'employment', 'experience', 'recommendation', 'achievement'
    ]
    
    # Check for certificate-related keywords
    keyword_matches = [kw for kw in certificate_keywords if kw in text_lower]
    
    if keyword_matches:
        detections.append({
            "class": "certificate_header",
            "confidence": 0.8,
            "text": ", ".join(keyword_matches[:3])
        })
    
    # Check for date
    if re.search(r'\d{2,4}[\s/-]?\d{2}[\s/-]?\d{2,4}', text):
        detections.append({
            "class": "date",
            "confidence": 0.7
        })
    
    # Check for name patterns
    if re.search(r'(name|awarded to|this is to certify that)[:\s]+[A-Z][a-z]+', text_lower):
        detections.append({
            "class": "name",
            "confidence": 0.7
        })
    
    return detections