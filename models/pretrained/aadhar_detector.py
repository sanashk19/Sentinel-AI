#!/usr/bin/env python3
"""
Aadhaar Card Detector - Detects and validates Aadhaar cards
"""

import re

def detect_aadhar(text):
    """
    Detect if text contains Aadhaar card number and return confidence score.
    
    Args:
        text (str): OCR extracted text from document
        
    Returns:
        dict: Contains detected status and confidence score
    """
    # Aadhaar format: 12 digits (often displayed as 4-4-4)
    aadhar_pattern = r"\b[2-9][0-9]{3}[\s-]?[0-9]{4}[\s-]?[0-9]{4}\b"
    
    match = re.search(aadhar_pattern, text if text else "")
    
    if not match:
        return {"detected": False, "confidence": 0.0}
    
    # Extract clean number
    aadhar_number = re.sub(r'[\s-]', '', match.group())
    
    # Basic Aadhaar validation (should start with 2-9, be 12 digits)
    confidence = 0.0
    
    if len(aadhar_number) == 12 and aadhar_number[0] in '23456789':
        confidence = 0.75  # Base confidence for valid Aadhaar format
        
        # Verhoeff algorithm check could be added here for checksum validation
        # For now, return base confidence
    
    return {
        "detected": True,
        "aadhar_number": aadhar_number[:4] + "XXXX" + aadhar_number[8:],  # Masked
        "confidence": confidence
    }
