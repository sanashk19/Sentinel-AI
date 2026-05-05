#!/usr/bin/env python3
"""
Sentinel AI - Neural Engine API Server
Agentic Architecture Implementation
"""

# Fix PyTorch 2.6+ weights_only security - patch torch.load BEFORE any imports
import torch
_original_torch_load = torch.load

def _patched_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)

torch.load = _patched_load

import os
import json
import base64
import tempfile
import numpy as np
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# Import the agentic pipeline
from agents.orchestrator import run_pipeline

app = Flask(__name__, static_folder='.')
CORS(app)


@app.route("/outputs/<path:filename>")
def serve_output_file(filename):
    return send_from_directory("outputs", filename)

# Serve static files (heatmaps, etc.)
@app.route('/<path:filename>', methods=['GET'])
def serve_static(filename):
    """Serve static files like heatmaps."""
    try:
        # Handle Windows paths
        filename = filename.replace('/', os.sep)
        if os.path.exists(filename):
            return send_file(filename)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'engine': 'agentic', 'architecture': 'multi-agent'}), 200

@app.route('/api/analyze', methods=['POST'])
def analyze_document():
    """
    Analyze document using the multi-agent pipeline.
    
    Maintains backwards compatibility with existing frontend.
    """
    try:
        data = request.get_json()
        image_data = data.get('image_data')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Decode base64
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # Save temp file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_file.write(image_bytes)
            tmp_path = tmp_file.name
        
        try:
            # Run the agentic pipeline
            result = run_pipeline(tmp_path)
            
            # Build response maintaining backwards compatibility
            response = {
                'forensic_score': result.get('forensic_score', 0),
                'ml_score': result.get('ml_score', 0),
                'pretrained_score': result.get('pretrained_score', 0),
                'validation_score': result.get('validation_score', 0),
                'trust_score': result.get('trust_score', 0),
                'status': result.get('status', 'UNKNOWN'),
                'document_type': result.get('document_type', 'UNKNOWN'),
                'ela_score': result.get('ela_score', 0),
                'anomaly_count': result.get('anomaly_count', 0),
                'checksum_valid': False,  # Deprecated but kept for compatibility
                'anomalies': result.get('anomalies', []),
                'ocr_text': result.get('ocr_text', ''),
                'doc_type': result.get('document_type', 'UNKNOWN'),
                'field_results': result.get('field_results', []),
                'detected_fields': result.get('detected_fields', []),  # Bounding boxes
                'heatmap': (result.get('heatmap', '') or '').replace('\\', '/'),  # Forensic heatmap
                'gradcam_heatmap': (result.get('gradcam_heatmap', '') or '').replace('\\', '/'),
                'reasoning': result.get('reasoning', []),  # Rule-based reasoning
                'ai_reasoning': result.get('ai_reasoning', ''),  # Gemini AI reasoning
                'signature_detected': result.get('signature_detected', False),
                'stamp_detected': result.get('stamp_detected', False),
                'stamp_signature_results': result.get('stamp_signature_results', {}),
                'structural_results': result.get('structural_results', {}),
                'dct_results': result.get('dct_results', {}),
                'summary': result.get('summary', ''),
                # Optional Florence semantic analysis (safe extras)
                'florence_enabled': result.get('florence_enabled', False),
                'florence_caption': result.get('florence_caption', ''),
                'florence_logo_detection': result.get('florence_logo_detection', None)
            }
            
            return jsonify(response), 200
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/download_report', methods=['GET'])
def download_report():
    report_path = "forensic_report.pdf"
    if not os.path.exists(report_path):
        return jsonify({"error": "Report not found"}), 404
    return send_file(
        report_path,
        as_attachment=True,
        download_name="forensic_report.pdf"
    )

if __name__ == '__main__':
    print("🚀 Starting Sentinel AI API Server (Agentic Architecture)...")
    print("🤖 Multi-agent pipeline initialized")
    print("🌐 Running on http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
