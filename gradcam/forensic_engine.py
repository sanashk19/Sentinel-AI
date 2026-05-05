#!/usr/bin/env python3
"""
Sentinel AI - Neural Engine for Document Forgery Detection
Author: Senior Forensic Vision Engineer
Dependencies: opencv-python, pytesseract, tensorflow, numpy, pillow, reportlab
"""

import cv2
import numpy as np
import pytesseract
# Set Tesseract path for macOS (Homebrew)
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing import image
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
import io
import base64
import json
from datetime import datetime
import re
import qrcode
from PIL import Image, ImageDraw, ImageFont
import argparse
import os

class SentinelNeuralEngine:
    def __init__(self):
        """Initialize Neural Engine with all detection modules"""
        self.confidence_threshold = 0.85
        self.trust_score = 0
        self.anomalies = []
        self.heatmap = None
        self.ela_image = None
        
        # Load pre-trained CNN for deep learning analysis
        self.load_deep_model()
        
    def load_deep_model(self):
        """Load pre-trained MobileNetV2 with Grad-CAM support"""
        # Build custom model with unique name to avoid conflicts
        base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
        
        # Add custom classification head
        x = tf.keras.layers.GlobalAveragePooling2D()(base_model.output)
        x = tf.keras.layers.Dense(128, activation='relu')(x)
        output = tf.keras.layers.Dense(2, activation='softmax')(x)
        
        self.forensic_cnn = Model(inputs=base_model.input, outputs=output, name='forensic_cnn')
        self.forensic_cnn.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        
        # Store layer names for Grad-CAM
        self.last_conv_layer = 'block_16_project'  # Deeper layer for finer granularity
        
    def ocr_validation(self, image_path):
        """OCR Validation using Tesseract with QR code cross-reference and checksums"""
        print("🔍 Running OCR Validation with Checksum Verification...")
        
        # Check if file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
            
        # Extract text using Tesseract
        extracted_text = pytesseract.image_to_string(img, config='--psm 6')
        
        validation_results = {
            'extracted_text': extracted_text,
            'data_tampering': False,
            'qr_payload': None,
            'mismatches': [],
            'checksum_valid': False
        }
        
        # Extract common document fields
        dob_match = re.search(r'\b(\d{2}[-/]\d{2}[-/]\d{4}|\d{8})\b', extracted_text)
        pan_match = re.search(r'\b[A-Z]{5}\d{4}[A-Z]\b', extracted_text)
        aadhaar_match = re.search(r'\b\d{4}\s\d{4}\s\d{4}\b', extracted_text)
        
        # AGGRESSIVE: Aadhaar Checksum Validation using Verhoeff algorithm
        if aadhaar_match:
            aadhaar_number = aadhaar_match.group(0).replace(' ', '')
            if len(aadhaar_number) == 12:
                is_valid = self.verify_aadhaar_checksum(aadhaar_number)
                validation_results['checksum_valid'] = is_valid
                if not is_valid:
                    validation_results['data_tampering'] = True
                    self.anomalies.append({
                        'type': 'AGGRESSIVE: Invalid Aadhaar Checksum - FAKE DOCUMENT',
                        'confidence': 1.0,
                        'description': f'Aadhaar number {aadhaar_number} fails Verhoeff checksum - document is FORGED',
                        'severity': 'CRITICAL'
                    })
        
        # Try to detect and decode QR code
        try:
            qr_detector = cv2.QRCodeDetector()
            data, points, _ = qr_detector.detectAndDecode(img)
            if data:
                validation_results['qr_payload'] = data
                
                # Cross-reference extracted data with QR payload
                if dob_match and dob_match.group(1) in data:
                    print("✅ DOB matches QR code")
                else:
                    validation_results['data_tampering'] = True
                    validation_results['mismatches'].append("DOB mismatch with QR code")
                    
                if pan_match and pan_match.group(0) in data:
                    print("✅ PAN matches QR code")
                else:
                    validation_results['data_tampering'] = True
                    validation_results['mismatches'].append("PAN mismatch with QR code")
                    
        except Exception as e:
            print(f"QR Code detection failed: {e}")
            
        return validation_results
    
    def verify_aadhaar_checksum(self, aadhaar_number):
        """Verify Aadhaar number using Verhoeff algorithm"""
        # Verhoeff multiplication table
        d = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
            [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
            [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
            [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
            [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
            [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
            [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
            [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
            [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        ]
        
        # Verhoeff permutation table
        p = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
            [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
            [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
            [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
            [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
            [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
            [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
        ]
        
        # Inverse table
        inv = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]
        
        c = 0
        for i, digit in enumerate(reversed(aadhaar_number)):
            c = d[c][p[i % 8][int(digit)]]
        
        return c == 0
    
    def structural_audit(self, image_path):
        """Structural Audit using OpenCV for edge detection and noise analysis"""
        print("🔬 Running Structural Audit...")
        
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        audit_results = {
            'canny_edges': None,
            'laplacian_variance': 0,
            'noise_estimate': 0,
            'digital_cut_detected': False,
            'rephotographed_screen': False
        }
        
        # Canny Edge Detection for digital cuts
        edges = cv2.Canny(gray, 50, 150)
        audit_results['canny_edges'] = edges
        
        # Calculate edge density in signature/photo regions
        edge_density = np.sum(edges > 0) / edges.size
        if edge_density > 0.15:  # High edge density suggests digital manipulation
            audit_results['digital_cut_detected'] = True
            self.anomalies.append({
                'type': 'Digital Cut Detected',
                'confidence': min(edge_density * 5, 1.0),
                'description': 'Unusual edge patterns suggest digital cutting/pasting'
            })
        
        # Laplacian Variance for blur detection (re-photographed screens)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        audit_results['laplacian_variance'] = variance
        
        if variance < 100:  # Low variance indicates blur/re-photography
            audit_results['rephotographed_screen'] = True
            self.anomalies.append({
                'type': 'Re-photographed Screen',
                'confidence': min((100 - variance) / 100, 1.0),
                'description': 'Document appears to be photographed from a screen'
            })
        
        # AGGRESSIVE: "Too Sharp" Rule - High Laplacian = digitally generated text
        if variance > 500:  # Extremely high variance indicates digital generation
            self.anomalies.append({
                'type': 'AGGRESSIVE: Too Sharp - Digitally Generated Text',
                'confidence': min((variance - 500) / 500, 1.0),
                'description': 'Text appears mathematically perfect - not captured by camera lens',
                'severity': 'CRITICAL'
            })
        
        # AGGRESSIVE: Canny 'Jitter' Detection - Check for mathematically straight edges
        self.detect_edge_jitter(edges)
        
        # AGGRESSIVE: RGB-Only Pixel Detection for digital overlays
        self.detect_rgb_only_pixels(img)
        
        # AGGRESSIVE: Sub-pixel Mismatch Detection (1% threshold)
        self.detect_subpixel_mismatch(img)
        
        # AGGRESSIVE: Font Kerning Mismatch Detection (2% threshold)
        self.detect_font_kerning_mismatch(img)
        
        # Gaussian Noise Estimator
        kernel = np.ones((5,5), np.float32) / 25
        filtered = cv2.filter2D(gray, -1, kernel)
        noise = np.std(gray.astype(float) - filtered.astype(float))
        audit_results['noise_estimate'] = noise
        
        if noise < 2:  # Unusually low noise suggests digital manipulation
            self.anomalies.append({
                'type': 'Low Noise Anomaly',
                'confidence': min((10 - noise) / 10, 1.0),
                'description': 'Sub-pixel inconsistencies detected in text fields'
            })
        
        return audit_results
    
    def error_level_analysis(self, image_path, quality=75):
        """Aggressive Error Level Analysis - 75% quality for obvious digital glow"""
        print("📊 Running Aggressive ELA Analysis (75% quality)...")
        
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
            
        # AGGRESSIVE: Save at 75% quality (lower = more obvious tampering)
        temp_path = "temp_ela.jpg"
        cv2.imwrite(temp_path, img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        
        # Read back and calculate difference
        compressed = cv2.imread(temp_path)
        ela = cv2.absdiff(img, compressed)
        ela = cv2.convertScaleAbs(ela, alpha=255/15.0)  # More aggressive scaling
        
        self.ela_image = ela
        
        # AGGRESSIVE: Lower threshold to catch more forgeries
        ela_score = np.mean(ela)
        
        if ela_score > 20:  # Lowered from 30
            self.anomalies.append({
                'type': 'AGGRESSIVE: High ELA Score - Digital Glow Detected',
                'confidence': min(ela_score / 35, 1.0),
                'description': 'Obvious digital editing artifacts - text shows compression glow',
                'severity': 'HIGH'
            })
        
        return ela
    
    def grad_cam_heatmap(self, image_path):
        """Generate granular, localized Grad-CAM heatmap for precise anomaly detection"""
        print("🧠 Sentinel-Alpha: Generating Localized Grad-CAM...")
        
        # Load and preprocess image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        orig_h, orig_w = img.shape[:2]
        
        # Resize for model input - ENSURE 224x224
        img_resized = cv2.resize(img, (224, 224))
        x = np.expand_dims(img_resized, axis=0)
        x = x.astype(np.float32)
        
        # Verify shape before prediction
        if x.shape != (1, 224, 224, 3):
            raise ValueError(f"Invalid input shape: {x.shape}, expected (1, 224, 224, 3)")
        
        x = tf.keras.applications.mobilenet_v2.preprocess_input(x)
        
        # Get prediction using forensic_cnn
        preds = self.forensic_cnn.predict(x, verbose=0)
        class_idx = np.argmax(preds[0])
        
        # Create Grad-CAM model using forensic_cnn
        grad_model = tf.keras.models.Model(
            [self.forensic_cnn.inputs], 
            [self.forensic_cnn.get_layer(self.last_conv_layer).output, self.forensic_cnn.output]
        )
        
        # Compute gradients with weighting
        with tf.GradientTape() as tape:
            conv_outputs, predictions = grad_model(x)
            loss = predictions[:, class_idx]
        
        grads = tape.gradient(loss, conv_outputs)
        
        # Weighted average of gradients
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
        
        # Convert to numpy for manipulation
        conv_outputs_np = conv_outputs.numpy()
        pooled_grads_np = pooled_grads.numpy()
        
        # Apply weights to feature maps (numpy version)
        for i in range(pooled_grads_np.shape[0]):
            conv_outputs_np[0, :, :, i] *= pooled_grads_np[i]
        
        # Create heatmap with ReLU and normalization
        heatmap = np.mean(conv_outputs_np[0], axis=-1)
        heatmap = np.maximum(heatmap, 0)
        heatmap /= (np.max(heatmap) + 1e-10)  # Avoid division by zero
        
        # Resize to original with cubic interpolation for smoothness
        heatmap_resized = cv2.resize(heatmap, (orig_w, orig_h), interpolation=cv2.INTER_CUBIC)
        
        # Threshold to get high-confidence regions (>60%)
        heatmap_thresh = np.where(heatmap_resized > 0.6, heatmap_resized, 0)
        
        # Create binary forensic mask
        forensic_mask = (heatmap_thresh > 0).astype(np.uint8) * 255
        
        # Clean up mask with morphological operations
        kernel = np.ones((5, 5), np.uint8)
        forensic_mask = cv2.morphologyEx(forensic_mask, cv2.MORPH_CLOSE, kernel)
        forensic_mask = cv2.morphologyEx(forensic_mask, cv2.MORPH_OPEN, kernel)
        
        # Store for later use
        self.localized_heatmap = heatmap_resized
        self.forensic_mask = forensic_mask
        
        # Apply JET colormap for standard visualization
        heatmap_vis = np.uint8(255 * heatmap_resized)
        heatmap_colored = cv2.applyColorMap(heatmap_vis, cv2.COLORMAP_JET)
        
        self.heatmap = heatmap_colored
        
        # Extract high-confidence regions
        high_conf_regions = self._extract_forensic_regions(heatmap_thresh)
        
        return {
            'heatmap': heatmap_colored,
            'raw_heatmap': heatmap_resized,
            'mask': forensic_mask,
            'high_confidence_regions': high_conf_regions
        }
    
    def _extract_forensic_regions(self, heatmap_thresh):
        """Extract bounding boxes of high-confidence forensic regions"""
        contours, _ = cv2.findContours(
            (heatmap_thresh > 0).astype(np.uint8), 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        regions = []
        for cnt in contours:
            if cv2.contourArea(cnt) > 100:  # Filter small noise
                x, y, w, h = cv2.boundingRect(cnt)
                confidence = float(np.mean(heatmap_thresh[y:y+h, x:x+w]))
                regions.append({
                    'bbox': [int(x), int(y), int(w), int(h)],
                    'confidence': confidence,
                    'area': int(cv2.contourArea(cnt))
                })
        
        return sorted(regions, key=lambda x: x['confidence'], reverse=True)
    
    def create_neon_forensic_overlay(self, image_path, output_path='forensic_overlay.png'):
        """
        Create neon red-to-transparent forensic overlay
        High-tech laser scan visualization for aggressive alerts
        """
        print("🎨 Creating Neon Forensic Overlay...")
        
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
        
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Ensure we have localized heatmap
        if not hasattr(self, 'localized_heatmap') or self.localized_heatmap is None:
            self.grad_cam_heatmap(image_path)
        
        # Normalize heatmap
        heatmap_norm = self.localized_heatmap / np.max(self.localized_heatmap) if np.max(self.localized_heatmap) > 0 else self.localized_heatmap
        
        # Create neon red overlay (255, 0, 60) with intensity
        overlay = np.zeros_like(img_rgb)
        overlay[:, :, 0] = (heatmap_norm * 255).astype(np.uint8)  # Red
        overlay[:, :, 1] = (heatmap_norm * 60).astype(np.uint8)   # Green (orange tint)
        overlay[:, :, 2] = (heatmap_norm * 20).astype(np.uint8)   # Blue
        
        # Alpha blending with max 70% opacity
        alpha = heatmap_norm[:, :, np.newaxis]
        alpha = np.clip(alpha * 2, 0, 0.7)
        
        # Blend
        blended = (img_rgb * (1 - alpha) + overlay * alpha).astype(np.uint8)
        
        # Add forensic mask contours
        if hasattr(self, 'forensic_mask') and self.forensic_mask is not None:
            contours, _ = cv2.findContours(
                self.forensic_mask, 
                cv2.RETR_EXTERNAL, 
                cv2.CHAIN_APPROX_SIMPLE
            )
            cv2.drawContours(blended, contours, -1, (255, 0, 60), 2)
        
        # Save with matplotlib for high quality
        plt.figure(figsize=(12, 8), facecolor='black')
        plt.imshow(blended)
        plt.axis('off')
        plt.title('Sentinel-Alpha Forensic Analysis', 
                 fontsize=14, fontweight='bold', color='white', pad=10)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                   facecolor='black', edgecolor='none')
        plt.close()
        
        return output_path
    
    def dct_analysis(self, image_path):
        """DCT coefficient analysis for double compression detection"""
        print("📈 Running DCT Analysis...")
        
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Resize to even dimensions for DCT
        h, w = img.shape
        if h % 2 != 0 or w % 2 != 0:
            new_h = h if h % 2 == 0 else h + 1
            new_w = w if w % 2 == 0 else w + 1
            img = cv2.resize(img, (new_w, new_h))
            
        # Apply DCT
        dct = cv2.dct(np.float32(img) / 255.0)
        
        # Analyze coefficient distribution
        coeffs = dct.flatten()
        hist, _ = np.histogram(coeffs, bins=50)
        
        # Detect spikes in histogram (indicates double compression)
        spike_threshold = np.mean(hist) + 3 * np.std(hist)
        spikes = np.sum(hist > spike_threshold)
        
        if spikes > 5:
            self.anomalies.append({
                'type': 'Double Compression',
                'confidence': min(spikes / 10, 1.0),
                'description': 'DCT analysis shows double compression artifacts'
            })
        
        return dct
    
    def detect_edge_jitter(self, edges):
        """AGGRESSIVE: Detect mathematically straight edges (digital) vs scanned noise (analog)"""
        print("🔍 Running Canny Jitter Detection...")
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        straight_edge_count = 0
        total_edges = 0
        
        for contour in contours:
            if len(contour) > 50:  # Only consider significant edges
                total_edges += 1
                # Approximate polygon
                epsilon = 0.01 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # If contour has very few vertices, it's likely a straight digital edge
                if len(approx) <= 4:
                    straight_edge_count += 1
        
        if total_edges > 0:
            straight_ratio = straight_edge_count / total_edges
            if straight_ratio > 0.6:  # If >60% edges are perfectly straight
                self.anomalies.append({
                    'type': 'AGGRESSIVE: Digital Edge Jitter - Mathematically Perfect',
                    'confidence': min(straight_ratio, 1.0),
                    'description': f'{straight_ratio*100:.1f}% of edges are perfectly straight - indicates digital creation',
                    'severity': 'HIGH'
                })
    
    def detect_rgb_only_pixels(self, img):
        """AGGRESSIVE: Detect pure RGB pixels indicating digital overlays"""
        print("🔍 Running RGB-Only Pixel Detection...")
        
        # Check for pure black (0,0,0) pixels in text regions
        # Real scans have noise, digital overlays are pure
        height, width = img.shape[:2]
        
        # Sample central region (where text usually is)
        y_start = int(height * 0.2)
        y_end = int(height * 0.8)
        x_start = int(width * 0.1)
        x_end = int(width * 0.9)
        
        roi = img[y_start:y_end, x_start:x_end]
        
        # Count pure black pixels (0,0,0)
        pure_black = np.sum(np.all(roi == [0, 0, 0], axis=2))
        total_pixels = roi.shape[0] * roi.shape[1]
        pure_black_ratio = pure_black / total_pixels
        
        # Count pixels where all channels are identical (digitally generated)
        diff_channels = np.abs(roi[:,:,0].astype(int) - roi[:,:,1].astype(int)) + \
                       np.abs(roi[:,:,1].astype(int) - roi[:,:,2].astype(int))
        identical_channels = np.sum(diff_channels < 5)  # Within 5 values
        identical_ratio = identical_channels / total_pixels
        
        if pure_black_ratio > 0.01 or identical_ratio > 0.15:
            self.anomalies.append({
                'type': 'AGGRESSIVE: RGB-Only Pixels - Digital Overlay Detected',
                'confidence': max(pure_black_ratio * 50, identical_ratio * 3),
                'description': f'Pure black: {pure_black_ratio*100:.2f}%, Identical channels: {identical_ratio*100:.1f}% - suggests digital overlay',
                'severity': 'HIGH'
            })
    
    def detect_subpixel_mismatch(self, img):
        """AGGRESSIVE: Detect 1% deviation in character kerning/alignment"""
        print("🔍 Running Sub-pixel Mismatch Detection (1% threshold)...")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get text regions
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find connected components (characters)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)
        
        if num_labels > 2:  # Ignore background
            # Calculate horizontal spacing between components
            x_positions = sorted([centroids[i][0] for i in range(1, num_labels)])
            
            if len(x_positions) > 2:
                spacings = [x_positions[i+1] - x_positions[i] for i in range(len(x_positions)-1)]
                avg_spacing = np.mean(spacings)
                spacing_variance = np.var(spacings)
                
                # 1% threshold check
                relative_variance = spacing_variance / (avg_spacing ** 2) if avg_spacing > 0 else 0
                
                if relative_variance > 0.0001:  # 1% threshold (0.01^2)
                    self.anomalies.append({
                        'type': 'AGGRESSIVE: Sub-pixel Mismatch Detected',
                        'confidence': min(relative_variance * 10000, 1.0),
                        'description': f'Character spacing variance: {relative_variance*100:.2f}% - exceeds 1% threshold',
                        'severity': 'CRITICAL'
                    })
    
    def detect_font_kerning_mismatch(self, img):
        """AGGRESSIVE: Font kerning mismatch detection - 2% threshold"""
        print("🔍 Running Font Kerning Mismatch Detection (2% threshold)...")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive threshold
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY_INV, 11, 2)
        
        # Find contours (characters)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter small noise
        char_contours = [c for c in contours if cv2.contourArea(c) > 50]
        
        if len(char_contours) > 3:
            # Get bounding boxes
            bboxes = [cv2.boundingRect(c) for c in char_contours]
            bboxes = sorted(bboxes, key=lambda b: b[0])  # Sort by x position
            
            # Calculate gaps between characters
            gaps = []
            for i in range(len(bboxes) - 1):
                gap = bboxes[i+1][0] - (bboxes[i][0] + bboxes[i][2])
                if gap > 0:
                    gaps.append(gap)
            
            if len(gaps) > 2:
                avg_gap = np.mean(gaps)
                gap_variance = np.var(gaps)
                
                # 2% threshold check
                relative_variance = gap_variance / (avg_gap ** 2) if avg_gap > 0 else 0
                
                if relative_variance > 0.0004:  # 2% threshold (0.02^2)
                    self.anomalies.append({
                        'type': 'AGGRESSIVE: Font Kerning Mismatch > 2%',
                        'confidence': min(relative_variance * 2500, 1.0),
                        'description': f'Font kerning variance: {relative_variance*100:.2f}% - exceeds 2% threshold, indicates font library mismatch',
                        'severity': 'CRITICAL'
                    })
                    return True
        return False
    
    def calculate_trust_score(self):
        """Calculate overall trust score - Gradual scoring based on high-confidence anomalies"""
        # Reduce false positives: only count anomalies that are confidently detected.
        # This keeps the same penalty curve but avoids penalizing weak signals.
        anomaly_count = sum(1 for a in self.anomalies if float(a.get('confidence', 0)) >= 0.75)
        
        # Gradual scoring: 0 anomalies = 100, each counted anomaly reduces by 15
        # 0 anomalies → 100, 1 → 85, 2 → 70, 3 → 55, 4 → 40, 5 → 25, 6+ → decreasing
        self.trust_score = max(0, 100 - (anomaly_count * 15))
        
        return self.trust_score
    
    def generate_forensic_report(self, image_path, output_path="forensic_report.pdf"):
        """Generate comprehensive PDF forensic report"""
        print("📄 Generating Forensic Report...")
        
        # Create PDF
        c = pdf_canvas.Canvas(output_path, pagesize=letter)
        width, height = letter
        
        # Header
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, "SENTINEL AI - FORENSIC ANALYSIS REPORT")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 80, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        c.drawString(50, height - 100, f"Document: {image_path}")
        
        # Trust Score
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 140, f"Trust Score: {self.trust_score:.1f}/100")
        
        # Color code trust score
        if self.trust_score >= 80:
            c.setFillColorRGB(0, 0.8, 0)  # Green
            status = "AUTHENTIC"
        elif self.trust_score >= 60:
            c.setFillColorRGB(1, 0.6, 0)  # Orange
            status = "NEEDS REVIEW"
        else:
            c.setFillColorRGB(1, 0, 0)  # Red
            status = "SUSPICIOUS"
        
        c.drawString(200, height - 140, status)
        c.setFillColorRGB(0, 0, 0)  # Reset to black
        
        # Anomalies Section
        y_pos = height - 180
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_pos, "DETECTED ANOMALIES:")
        y_pos -= 30
        
        c.setFont("Helvetica", 11)
        for anomaly in self.anomalies:
            c.drawString(70, y_pos, f"• {anomaly['type']}")
            c.drawString(90, y_pos - 15, f"Confidence: {anomaly['confidence']*100:.1f}%")
            c.drawString(90, y_pos - 30, f"Description: {anomaly['description']}")
            y_pos -= 50
        
        # Add images if available
        if self.ela_image is not None:
            y_pos -= 20
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_pos, "Error Level Analysis (ELA):")
            y_pos -= 20
            
            # Save ELA image temporarily
            ela_temp = "ela_temp.png"
            cv2.imwrite(ela_temp, self.ela_image)
            
            try:
                c.drawImage(ImageReader(ela_temp), 50, y_pos - 200, width=200, height=150)
            except:
                pass
            y_pos -= 220
        
        if self.heatmap is not None:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_pos, "Grad-CAM Heatmap:")
            y_pos -= 20
            
            # Save heatmap temporarily
            heat_temp = "heatmap_temp.png"
            cv2.imwrite(heat_temp, self.heatmap)
            
            try:
                c.drawImage(ImageReader(heat_temp), 50, y_pos - 200, width=200, height=150)
            except:
                pass
        
        # Save PDF
        c.save()
        print(f"✅ Report saved to: {output_path}")
        
        return output_path
    
    def analyze_document(self, image_path):
        """Complete forensic analysis pipeline"""
        print("🚀 Starting Sentinel AI Neural Engine Analysis...")
        print("=" * 60)
        
        # Reset state
        self.anomalies = []
        self.trust_score = 0
        
        try:
            # 1. OCR Validation
            ocr_results = self.ocr_validation(image_path)
            
            # 2. Structural Audit
            structural_results = self.structural_audit(image_path)
            
            # 3. Error Level Analysis
            ela_results = self.error_level_analysis(image_path)
            ela_score = np.mean(np.abs(ela_results)) if ela_results is not None else 0
            
            # 4. Grad-CAM Analysis
            heatmap = self.grad_cam_heatmap(image_path)
            
            # 5. DCT Analysis
            dct_results = self.dct_analysis(image_path)
            
            # 6. Calculate Trust Score
            trust_score = self.calculate_trust_score()
            
            # 7. Generate Report
            report_path = self.generate_forensic_report(image_path)
            
            print("=" * 60)
            print(f"✅ Analysis Complete!")
            print(f"📊 Trust Score: {trust_score:.1f}/100")
            print(f"🚨 Anomalies Detected: {len(self.anomalies)}")
            print(f"📄 Report: {report_path}")
            
            return {
                'trust_score': trust_score,
                'anomalies': self.anomalies,
                'ocr_results': ocr_results,
                'structural_results': structural_results,
                'ela_score': ela_score,
                'dct_results': dct_results,
                'ela_available': ela_results is not None,
                'heatmap_available': heatmap is not None,
                'report_path': report_path
            }
            
        except Exception as e:
            print(f"❌ Analysis Failed: {e}")
            return {'error': str(e)}

# Usage Example
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sentinel AI Neural Engine - Document Forgery Detection')
    parser.add_argument('--document', type=str, required=True, help='Path to document image')
    args = parser.parse_args()
    
    engine = SentinelNeuralEngine()
    
    # Analyze document
    results = engine.analyze_document(args.document)
    
    if 'error' not in results:
        print("\n🎯 Analysis Results:")
        print(f"Trust Score: {results['trust_score']}/100")
        print(f"Anomalies: {len(results['anomalies'])}")
        for anomaly in results['anomalies']:
            print(f"  - {anomaly['type']}: {anomaly['confidence']*100:.1f}%")
