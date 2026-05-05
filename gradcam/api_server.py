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

# Import the forensic engine and ML engine directly
from forensic_engine import SentinelNeuralEngine
from ml_engine import analyze_ml

app = Flask(__name__, static_folder='.')
CORS(app)

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
    return jsonify({'status': 'ok', 'engine': 'forensic', 'architecture': 'direct'}), 200

@app.route('/api/analyze', methods=['POST'])
def analyze_document():
    """
    Analyze document using the forensic engine directly.
    
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
            # Initialize forensic engine
            engine = SentinelNeuralEngine()
            
            # Run forensic analysis
            result = engine.analyze_document(tmp_path)
            
            # Generate neon forensic overlay
            heatmap_path = engine.create_neon_forensic_overlay(tmp_path, 'outputs/forensic_heatmap.png')
            
            # Run ML analysis
            ml_result = analyze_ml(tmp_path)
            
            def serialize_result(obj):
                """Convert numpy arrays and other non-serializable objects to JSON-serializable format"""
                if hasattr(obj, 'tolist'):
                    return obj.tolist()
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, dict):
                    return {key: serialize_result(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [serialize_result(item) for item in obj]
                else:
                    return obj
            
            # Build response maintaining backwards compatibility
            response = {
                'trust_score': result.get('trust_score', 0),
                'status': result.get('status', 'UNKNOWN'),
                'document_type': result.get('document_type', 'UNKNOWN'),
                'ela_score': result.get('ela_score', 0),
                'anomaly_count': len(result.get('anomalies', [])),
                'checksum_valid': False,
                'anomalies': result.get('anomalies', []),
                'ocr_text': result.get('ocr_text', ''),
                'doc_type': result.get('document_type', 'UNKNOWN'),
                'field_results': result.get('field_results', []),
                'detected_fields': result.get('detected_fields', []),
                'heatmap': 'outputs/forensic_heatmap.png',
                'heatmap_url': '/outputs/forensic_heatmap.png',
                'reasoning': result.get('reasoning', []),
                'structural_results': serialize_result(result.get('structural_results', {})),
                'dct_results': serialize_result(result.get('dct_results', {})),
                'summary': result.get('summary', ''),
                # Use actual ML and forensic scores
                'forensic_score': result.get('trust_score', 0),
                'ml_score': int((1 - ml_result.get('ml_score', 0.5)) * 100),  # Invert: 0=genuine, 1=forged
                'pretrained_score': 50,  # Neutral score
                'validation_score': 50,  # Neutral score
                'ai_reasoning': result.get('summary', '')
            }
            
            # Serialize the response to handle numpy arrays
            response = serialize_result(response)
            
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
    print("🚀 Starting Sentinel AI API Server (Direct Mode)...")
    print("🔍 Forensic engine initialized")
    print("🌐 Running on http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
