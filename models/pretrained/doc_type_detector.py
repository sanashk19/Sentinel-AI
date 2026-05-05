#!/usr/bin/env python3
"""
Document Type Detector - Identifies document type from OCR text
"""

import re

def detect_document_type(text):
    """
    Detect the type of document based on OCR text content.
    
    Args:
        text (str): OCR extracted text from document
        
    Returns:
        str: Document type - "PAN", "AADHAAR", "CERTIFICATE", or "UNKNOWN"
    """
    if not text:
        return "UNKNOWN"
    
    text_upper = text.upper()
    
    # PAN card indicators
    pan_keywords = ['INCOME TAX', 'PAN', 'PERMANENT ACCOUNT NUMBER', 'INCOMETAXDEPARTMENT']
    pan_pattern = r"[A-Z]{5}[0-9]{4}[A-Z]{1}"
    
    if re.search(pan_pattern, text_upper) or any(kw in text_upper for kw in pan_keywords):
        return "PAN"
    
    # Aadhaar card indicators
    aadhar_keywords = ['AADHAAR', 'AADHAR', 'UID', 'UNIQUE IDENTIFICATION']
    aadhar_pattern = r"\b[2-9][0-9]{3}[\s-]?[0-9]{4}[\s-]?[0-9]{4}\b"
    
    if re.search(aadhar_pattern, text) or any(kw in text_upper for kw in aadhar_keywords):
        return "AADHAAR"
    
    # Certificate indicators
    certificate_keywords = [
        'CERTIFICATE', 'DEGREE', 'DIPLOMA', 'GRADUATION',
        'BACHELOR', 'MASTER', 'DOCTORATE', 'AWARDED', 'CERTIFY'
    ]
    
    if any(kw in text_upper for kw in certificate_keywords):
        return "CERTIFICATE"
    
    return "UNKNOWN"
