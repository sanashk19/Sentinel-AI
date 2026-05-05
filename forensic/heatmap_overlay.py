#!/usr/bin/env python3
"""
Forensic Heatmap Overlay Generator
Generates visual heatmap overlays for document anomaly visualization
"""

import cv2
import numpy as np
import os


def generate_heatmap_overlay(image_path: str, anomaly_mask: np.ndarray = None) -> str:
    """
    Generate a forensic heatmap overlay on the document image.
    
    Args:
        image_path: Path to the original document image
        anomaly_mask: Optional numpy array with anomaly regions (same size as image)
                     If None, generates a gradient-based heatmap
    
    Returns:
        str: Path to the generated heatmap overlay image
    """
    try:
        # Read original image
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Create anomaly mask if not provided
        if anomaly_mask is None:
            # Generate gradient-based heatmap for visualization
            h, w = image.shape[:2]
            
            # Create a gradient mask simulating anomaly regions
            anomaly_mask = np.zeros((h, w), dtype=np.uint8)
            
            # Add some random anomaly regions for visualization
            # In production, this would come from actual forensic analysis
            center_x, center_y = w // 2, h // 2
            
            # Create elliptical anomaly region
            cv2.ellipse(anomaly_mask, (center_x, center_y), 
                       (w // 4, h // 6), 0, 0, 360, 255, -1)
            
            # Add some noise for realism
            noise = np.random.randint(0, 50, (h, w), dtype=np.uint8)
            anomaly_mask = cv2.add(anomaly_mask, noise)
            
            # Apply Gaussian blur for smooth transitions
            anomaly_mask = cv2.GaussianBlur(anomaly_mask, (21, 21), 0)
        
        # Ensure anomaly mask is the right size
        h, w = image.shape[:2]
        if anomaly_mask.shape[:2] != (h, w):
            anomaly_mask = cv2.resize(anomaly_mask, (w, h))
        
        # Normalize mask to 0-255 range
        if anomaly_mask.max() > 0:
            anomaly_mask = ((anomaly_mask / anomaly_mask.max()) * 255).astype(np.uint8)
        
        # Apply colormap to create heatmap
        heatmap = cv2.applyColorMap(anomaly_mask, cv2.COLORMAP_JET)
        
        # Blend original image with heatmap
        overlay = cv2.addWeighted(image, 0.7, heatmap, 0.3, 0)
        
        # Ensure output directory exists
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output path
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_heatmap.png")
        
        # Save overlay
        cv2.imwrite(output_path, overlay)
        
        print(f"[Heatmap] Generated heatmap overlay: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"[Heatmap] Error generating heatmap: {e}")
        return ""


def generate_ela_heatmap(image_path: str, ela_result: dict) -> str:
    """
    Generate heatmap from Error Level Analysis results.
    
    Args:
        image_path: Path to the original image
        ela_result: Dictionary containing ELA analysis results
    
    Returns:
        str: Path to generated heatmap
    """
    try:
        # Extract ELA data if available
        ela_score = ela_result.get("ela_score", 0)
        ela_image = ela_result.get("ela_image", None)
        
        if ela_image is not None:
            # Use the ELA image directly
            return generate_heatmap_overlay(image_path, ela_image)
        else:
            # Create synthetic heatmap based on score
            image = cv2.imread(image_path)
            if image is None:
                return ""
            
            h, w = image.shape[:2]
            
            # Create mask based on ELA score
            intensity = int(min(ela_score * 2.55, 255))  # Scale to 0-255
            anomaly_mask = np.full((h, w), intensity, dtype=np.uint8)
            
            return generate_heatmap_overlay(image_path, anomaly_mask)
            
    except Exception as e:
        print(f"[Heatmap] Error generating ELA heatmap: {e}")
        return ""


def generate_anomaly_heatmap(image_path: str, anomalies: list) -> str:
    """
    Generate heatmap from detected anomaly regions.
    
    Args:
        image_path: Path to the original image
        anomalies: List of anomaly dictionaries with region info
    
    Returns:
        str: Path to generated heatmap
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            return ""
        
        h, w = image.shape[:2]
        anomaly_mask = np.zeros((h, w), dtype=np.uint8)
        
        # Mark anomaly regions on the mask
        for anomaly in anomalies:
            # Check if anomaly has region info
            if "region" in anomaly:
                x, y, rw, rh = anomaly["region"]
                confidence = anomaly.get("confidence", 0.5)
                intensity = int(confidence * 255)
                cv2.rectangle(anomaly_mask, (x, y), (x + rw, y + rh), intensity, -1)
            elif "bbox" in anomaly:
                x1, y1, x2, y2 = anomaly["bbox"]
                confidence = anomaly.get("confidence", 0.5)
                intensity = int(confidence * 255)
                cv2.rectangle(anomaly_mask, (x1, y1), (x2, y2), intensity, -1)
        
        # Apply Gaussian blur for smooth transitions
        anomaly_mask = cv2.GaussianBlur(anomaly_mask, (21, 21), 0)
        
        return generate_heatmap_overlay(image_path, anomaly_mask)
        
    except Exception as e:
        print(f"[Heatmap] Error generating anomaly heatmap: {e}")
        return ""
