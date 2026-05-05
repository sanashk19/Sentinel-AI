# Sentinel AI Neural Engine - Forensic Document Analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- macOS/Linux/Windows

### Setup & Installation

```bash
# Clone/Download the project
cd "senitel ai"

# Create virtual environment
python3 -m venv sentinel_env

# Activate virtual environment
source sentinel_env/bin/activate  # On Windows: sentinel_env\Scripts\activate

# Install dependencies
pip install opencv-python numpy tensorflow pytesseract flask flask-cors reportlab pillow

# Install Tesseract OCR (macOS)
brew install tesseract
# On Ubuntu/Debian:
# sudo apt-get install tesseract-ocr
# On Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
```

## 🏃‍♂️ Running the Application

### Method 1: Manual Start (Recommended)

```bash
# Terminal 1: Start API Server
source sentinel_env/bin/activate
python3 api_server.py

# Terminal 2: Start Web Server
python3 -m http.server 3000
```

### Method 2: One-Command Start

```bash
# Start both servers in background
source sentinel_env/bin/activate && python3 api_server.py &
python3 -m http.server 3000 &
```

## 🌐 Access the Dashboard

Open your browser and navigate to:
```
http://localhost:3000/dashboard.html
```

## 📊 Features

### 🔍 Aggressive Forensic Detection
- **Error Level Analysis (ELA)** - 75% quality resave threshold
- **Canny Edge Jitter Detection** - Mathematically perfect edges
- **Sub-pixel Mismatch** - 1% character spacing variance
- **RGB-Only Pixel Detection** - Digital overlay detection
- **Font Kerning Analysis** - 2% threshold mismatch
- **OCR Checksum Validation** - Verhoeff algorithm for Aadhaar
- **Laplacian Variance** - "Too Sharp" rule detection

### 📈 Tesla-Style Dashboard
- Real-time trust score (0-100)
- Color-coded anomaly severity
- Interactive anomaly list
- PDF report generation
- Live analysis progress

## 🧪 Testing

### Test with Sample Documents
```bash
# Test with included samples
python3 forensic_engine.py /path/to/your/document.jpg
```

### API Endpoints
```bash
# Health check
curl http://localhost:5001/api/health

# Analyze document
curl -X POST http://localhost:5001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"image_data": "base64_encoded_image"}'
```

## 🔧 Configuration

### Adjust Detection Sensitivity
Edit `forensic_engine.py`:
```python
# ELA quality threshold (default: 75)
error_level_analysis(image_path, quality=75)

# Sub-pixel mismatch threshold (default: 1%)
if relative_variance > 0.0001:  # 1% threshold

# Font kerning threshold (default: 2%)
if relative_variance > 0.0004:  # 2% threshold
```

### Trust Score Calculation
Edit `calculate_trust_score()` in `forensic_engine.py`:
```python
# Base score for clean documents
self.trust_score = 95

# Penalty multipliers
penalty = sum(a['confidence'] * 15 for a in self.anomalies)
```

## 📄 API Response Format

```json
{
  "trust_score": 85,
  "status": "AUTHENTIC",
  "ela_score": 12.5,
  "anomaly_count": 2,
  "checksum_valid": true,
  "anomalies": [
    {
      "type": "AGGRESSIVE: RGB-Only Pixels",
      "confidence": 0.85,
      "description": "Digital overlay detected",
      "severity": "HIGH"
    }
  ],
  "ocr_text": "Extracted text content...",
  "structural_results": {...},
  "dct_results": [...]
}
```

## 🐛 Troubleshooting

### Common Issues

1. **"API Error: Load failed"**
   ```bash
   # Check if API server is running
   curl http://localhost:5001/api/health
   
   # Restart API server
   pkill -f api_server.py
   python3 api_server.py
   ```

2. **"Object of type ndarray is not JSON serializable"**
   - Fixed in latest version - ensure you're using updated `api_server.py`

3. **Tesseract not found**
   ```bash
   # macOS
   brew install tesseract
   
   # Check installation
   tesseract --version
   ```

4. **Port already in use**
   ```bash
   # Kill processes on ports 3000 and 5001
   lsof -ti:3000,5001 | xargs kill -9
   ```

5. **Virtual environment issues**
   ```bash
   # Recreate environment
   rm -rf sentinel_env
   python3 -m venv sentinel_env
   source sentinel_env/bin/activate
   pip install -r requirements.txt
   ```

## 📁 Project Structure

```
senitel ai/
├── api_server.py              # Flask API backend
├── forensic_engine.py         # Core forensic analysis engine
├── dashboard.html             # Main dashboard UI
├── style.css                  # Dashboard styles
├── script.js                  # Frontend JavaScript
├── login.html                 # Login page
├── forensic.html              # Detailed analysis view
├── sentinel_env/              # Python virtual environment
├── forensic_report.pdf        # Generated reports
└── README.md                  # This file
```

## 🎯 Performance Tips

1. **For faster analysis:**
   - Reduce image size before upload
   - Use JPEG format (smaller files)
   - Close other applications to free RAM

2. **For better accuracy:**
   - Ensure good lighting in document photos
   - Avoid shadows and glare
   - Use high-resolution images (300+ DPI)

## 🔒 Security Notes

- All processing happens locally on your machine
- No data is sent to external servers
- Temporary files are automatically deleted
- PDF reports are saved locally only

## 📞 Support

For issues:
1. Check the troubleshooting section above
2. Ensure all dependencies are installed
3. Verify both servers are running on correct ports
4. Check browser console for JavaScript errors

---

**Sentinel AI Neural Engine** - Advanced Document Forensic Analysis
*Version 1.0* | *Aggressive Detection Mode*


# Sentinel-AI Grad-CAM Integration Guide (Sentinel-Alpha)

This project includes a localized Grad-CAM pipeline that generates:
1) a raw heatmap (model attention)
2) a binary mask of high-confidence regions
3) a neon red overlay image used by the dashboard

## Where Grad-CAM is implemented

### 1) Core Grad-CAM + Overlay (Python)
**File:** [forensic_engine.py](cci:7://file:///Users/jiya/Downloads/senitel%20ai/forensic_engine.py:0:0-0:0)  
**Class:** [SentinelNeuralEngine](cci:2://file:///Users/jiya/Downloads/senitel%20ai/forensic_engine.py:31:0-763:36)

Key functions:
- [load_deep_model()](cci:1://file:///Users/jiya/Downloads/senitel%20ai/forensic_engine.py:43:4-59:87)
  - Builds the CNN used for Grad-CAM (224x224 input)
  - Model stored in: `self.forensic_cnn`
  - Last conv layer used: `self.last_conv_layer`

- [grad_cam_heatmap(image_path)](cci:1://file:///Users/jiya/Downloads/senitel%20ai/forensic_engine.py:278:4-365:9)
  - Loads image via OpenCV
  - Resizes to 224x224
  - Runs prediction on `self.forensic_cnn`
  - Builds `grad_model` to fetch:
    - last conv outputs
    - model predictions
  - Computes gradients and creates normalized heatmap
  - Resizes heatmap back to original image size
  - Produces:
    - `self.localized_heatmap` (float heatmap, original size)
    - `self.forensic_mask` (thresholded + morphology cleaned mask)
    - `self.heatmap` (JET colormap visualization)
  - Returns a dict with:
    - `raw_heatmap`
    - `mask`
    - `high_confidence_regions` (bounding boxes)

- [create_neon_forensic_overlay(image_path, output_path=...)](cci:1://file:///Users/jiya/Downloads/senitel%20ai/forensic_engine.py:381:4-438:26)
  - Uses `self.localized_heatmap` to create neon red overlay
  - Uses matplotlib (Agg backend) to export image to disk
  - Used by the dashboard as the “Heatmap” view

- [analyze_document(image_path)](cci:1://file:///Users/jiya/Downloads/senitel%20ai/api_server.py:48:0-141:46)
  - Runs full forensic pipeline and calls [grad_cam_heatmap()](cci:1://file:///Users/jiya/Downloads/senitel%20ai/forensic_engine.py:278:4-365:9)

---

## How Grad-CAM is exposed to the frontend

### 2) API integration (Flask)
**File:** [api_server.py](cci:7://file:///Users/jiya/Downloads/senitel%20ai/api_server.py:0:0-0:0)

- Endpoint: `POST /api/analyze`
  - Creates [SentinelNeuralEngine()](cci:2://file:///Users/jiya/Downloads/senitel%20ai/forensic_engine.py:31:0-763:36)
  - Calls: [engine.analyze_document(tmp_path)](cci:1://file:///Users/jiya/Downloads/senitel%20ai/api_server.py:48:0-141:46)
  - Calls: [engine.create_neon_forensic_overlay(tmp_path, 'outputs/forensic_heatmap.png')](cci:1://file:///Users/jiya/Downloads/senitel%20ai/forensic_engine.py:381:4-438:26)
  - Returns JSON including:
    - `heatmap`: `outputs/forensic_heatmap.png`
    - `heatmap_url`: `/outputs/forensic_heatmap.png`

- Static serving:
  - `@app.route('/<path:filename>')` serves the generated heatmap image file paths.

---

## How the dashboard shows Grad-CAM

### 3) Frontend toggle + display
**File:** [dashboard.html](cci:7://file:///Users/jiya/Downloads/senitel%20ai/dashboard.html:0:0-0:0)

Key elements:
- Toggle buttons:
  - `btn-original`
  - `btn-heatmap`
- Overlay image:
  - `heatmapOverlay` (positioned absolute above the original preview)
- Functions:
  - [toggleHeatmap(view)](cci:1://file:///Users/jiya/Downloads/senitel%20ai/dashboard.html:1178:8-1200:9) switches between original + overlay
  - [displayNeuralResults(results)](cci:1://file:///Users/jiya/Downloads/senitel%20ai/dashboard.html:852:8-1084:9) loads heatmap URL and assigns it to:
    - `heatmapImage` (preview section)
    - `heatmapOverlay` (toggle overlay)
    - `heatmapImageResults` (results section)
  - A cache-buster is appended (`?t=...`) so the latest heatmap loads

Heatmap gating:
- Heatmap is only enabled if `trust_score <= 50`
- If `trust_score > 50`, heatmap UI is hidden/disabled

---

## Quick test

1) Start API:
```bash
source sentinel_env/bin/activate
python3 api_server.py