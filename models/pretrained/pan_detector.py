#!/usr/bin/env python3
"""
PAN Card Detector - Validates PAN card format and authenticity
"""

import re

def check_pan(text):
    """
    Check if text contains a valid PAN number and return confidence score.
    
    Args:
        text (str): OCR extracted text from document
        
    Returns:
        dict: Contains pan_number, confidence, and validity status
    """
    pan_pattern = r"[A-Z]{5}[0-9]{4}[A-Z]{1}"
    
    # OCR often introduces spaces/newlines between PAN characters.
    # Normalize to alphanumeric-only for robust matching.
    normalized = re.sub(r"[^A-Z0-9]", "", (text or "").upper())
    match = re.search(pan_pattern, normalized)
    
    if not match:
        return {"valid": False, "confidence": 0.0, "reason": "PAN format not found"}
    
    pan_number = match.group()
    
    # Basic validation - valid PAN format found
    confidence = 0.7  # Base confidence for valid PAN format
    
    return {
        "pan_number": pan_number,
        "confidence": confidence,
        "valid": True
    }