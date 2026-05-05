// ==========================================
// SENTINEL AI - FORENSIC ANALYSIS ENGINE
// ==========================================

// Speech Synthesis
function speak(text) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const msg = new SpeechSynthesisUtterance(text);
        msg.rate = 0.9;
        msg.pitch = 1;
        window.speechSynthesis.speak(msg);
    }
}

// Archive Management
function saveToArchive(data) {
    let archive = JSON.parse(localStorage.getItem('archive') || '[]');
    archive.unshift(data);
    localStorage.setItem('archive', JSON.stringify(archive));
}

// Load OpenCV
let cvLoaded = false;
function loadOpenCV() {
    return new Promise((resolve) => {
        if (cvLoaded) { resolve(); return; }
        const script = document.createElement('script');
        script.src = 'https://docs.opencv.org/4.8.0/opencv.js';
        script.onload = () => { cvLoaded = true; resolve(); };
        script.onerror = () => resolve();
        document.head.appendChild(script);
    });
}

// Forensic Analyzer Class
class ForensicAnalyzer {
    constructor() {
        this.results = { authenticity: 0, manipulations: [], scores: {} };
    }

    // Error Level Analysis
    async performELA(imageElement, canvasId) {
        const canvas = document.getElementById(canvasId);
        const ctx = canvas.getContext('2d');
        canvas.width = imageElement.naturalWidth || imageElement.width;
        canvas.height = imageElement.naturalHeight || imageElement.height;
        ctx.drawImage(imageElement, 0, 0);
        
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        const anomalies = [];
        
        for (let y = 1; y < canvas.height - 1; y += 2) {
            for (let x = 1; x < canvas.width - 1; x += 2) {
                const idx = (y * canvas.width + x) * 4;
                const neighbors = [
                    ((y - 1) * canvas.width + x) * 4,
                    ((y + 1) * canvas.width + x) * 4,
                    (y * canvas.width + (x - 1)) * 4,
                    (y * canvas.width + (x + 1)) * 4
                ];
                
                let variance = 0;
                for (let n of neighbors) {
                    variance += Math.abs(data[idx] - data[n]);
                }
                variance /= 4;
                
                if (variance > 25) {
                    data[idx] = 255;
                    data[idx + 1] = Math.max(0, 255 - variance * 2);
                    data[idx + 2] = Math.max(0, 255 - variance * 2);
                    if (variance > 50) anomalies.push({ x, y, intensity: variance });
                }
            }
        }
        
        ctx.putImageData(imageData, 0, 0);
        
        // Draw boxes
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 3;
        const regions = this.clusterAnomalies(anomalies);
        regions.forEach(r => {
            ctx.strokeRect(r.x - 25, r.y - 25, 50, 50);
            ctx.fillStyle = 'rgba(239, 68, 68, 0.3)';
            ctx.fillRect(r.x - 25, r.y - 25, 50, 50);
        });
        
        return { anomalyCount: anomalies.length, regions: regions.length, score: Math.min(100, anomalies.length / 50) };
    }

    clusterAnomalies(anomalies) {
        if (anomalies.length === 0) return [];
        const clusters = [];
        const visited = new Set();
        
        anomalies.forEach((a, i) => {
            if (visited.has(i)) return;
            const cluster = [a];
            visited.add(i);
            
            anomalies.forEach((o, j) => {
                if (visited.has(j)) return;
                const dist = Math.sqrt(Math.pow(a.x - o.x, 2) + Math.pow(a.y - o.y, 2));
                if (dist < 60) { cluster.push(o); visited.add(j); }
            });
            
            clusters.push({
                x: cluster.reduce((s, p) => s + p.x, 0) / cluster.length,
                y: cluster.reduce((s, p) => s + p.y, 0) / cluster.length,
                count: cluster.length
            });
        });
        
        return clusters.slice(0, 5);
    }

    async analyzeImage(imageElement, file, canvasId) {
        await loadOpenCV();
        
        const ela = await this.performELA(imageElement, canvasId);
        
        const results = {
            timestamp: new Date().toLocaleString(),
            ela,
            verdict: ela.anomalyCount > 100 ? 'SUSPICIOUS' : 'AUTHENTIC',
            confidence: Math.max(0, 100 - ela.score)
        };
        
        localStorage.setItem('forensicResults', JSON.stringify(results));
        return results;
    }
}

window.ForensicAnalyzer = ForensicAnalyzer;
window.forensicAnalyzer = new ForensicAnalyzer();
window.speak = speak;
window.saveToArchive = saveToArchive;
window.loadOpenCV = loadOpenCV;

// ==========================================
// NEURAL ENGINE INTEGRATION
// ==========================================

// Run Python Neural Engine Analysis
async function runNeuralEngineAnalysis(imagePath) {
    console.log('🧠 Running Neural Engine Analysis...');
    
    try {
        // Store analysis status
        localStorage.setItem('neuralEngineStatus', 'running');
        
        // Prepare form data with image
        const formData = new FormData();
        
        // Handle different image input types
        if (imagePath instanceof File) {
            formData.append('file', imagePath);
        } else if (typeof imagePath === 'string') {
            // If it's a base64 string or URL, fetch and convert to blob
            if (imagePath.startsWith('data:')) {
                const response = await fetch(imagePath);
                const blob = await response.blob();
                formData.append('file', blob, 'image.png');
            } else {
                // Assume it's a file path or URL
                const response = await fetch(imagePath);
                const blob = await response.blob();
                formData.append('file', blob);
            }
        }
        
        // Call real backend API
        const response = await fetch('http://127.0.0.1:5001/api/analyze', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('API failed with status: ' + response.status);
        }
        
        const data = await response.json();
        
        // Store MINIMAL DATA ONLY to avoid localStorage quota error
        const minimalData = {
            trust_score: data.forensic_score || 0,
            ml_score: data.ml_score || 0,
            anomalies: (data.anomalies || []).map(a => ({
                type: a.type,
                severity: a.severity,
                confidence: a.confidence
            })),
            status: data.status || 'UNKNOWN'
        };
        
        localStorage.setItem('neuralEngineResults', JSON.stringify(minimalData));
        localStorage.setItem('neuralEngineStatus', 'complete');
        
        return minimalData;
    } catch (error) {
        console.error('Neural Engine Error:', error);
        localStorage.setItem('neuralEngineStatus', 'error');
        return null;
    }
}

// Update Dashboard with Neural Results
function updateDashboardWithNeuralResults(results) {
    if (!results) return;
    
    // Update Trust Score
    const trustScoreEl = document.getElementById('trust-score');
    if (trustScoreEl) {
        trustScoreEl.textContent = results.trust_score + '/100';
        trustScoreEl.className = results.trust_score < 60 ? 'metric-danger' : 
                                  results.trust_score < 80 ? 'metric-warning' : 'metric-good';
    }
    
    // Update Status Badge
    const statusBadge = document.getElementById('status-badge');
    if (statusBadge) {
        statusBadge.textContent = results.status;
        statusBadge.className = 'status-badge ' + 
            (results.status === 'AUTHENTIC' ? 'status-pass' : 
             results.status === 'NEEDS REVIEW' ? 'status-review' : 'status-fail');
    }
    
    // Update Anomaly List
    const anomalyList = document.getElementById('anomaly-list');
    if (anomalyList && results.anomalies) {
        anomalyList.innerHTML = results.anomalies.map(anomaly => `
            <div class="anomaly-item" style="border-left: 4px solid ${anomaly.severity === 'CRITICAL' ? '#dc2626' : '#f59e0b'}; background: ${anomaly.severity === 'CRITICAL' ? '#fef2f2' : '#fffbeb'}; padding: 1rem; margin-bottom: 0.75rem; border-radius: 8px;">
                <strong style="color: ${anomaly.severity === 'CRITICAL' ? '#991b1b' : '#92400e'};">${anomaly.type}</strong>
                <p style="margin: 0.5rem 0 0 0; color: #7f1d1d; font-size: 0.9rem;">${anomaly.description}</p>
                <div style="margin-top: 0.5rem; font-family: monospace; font-size: 0.8rem; color: #9ca3af;">
                    Confidence: ${(anomaly.confidence * 100).toFixed(1)}% | Severity: ${anomaly.severity}
                </div>
            </div>
        `).join('');
    }
    
    // Update ELA Score
    const elaScoreEl = document.getElementById('ela-score');
    if (elaScoreEl) {
        elaScoreEl.textContent = results.ela_score?.toFixed(1) || '--';
    }
    
    // Speak results
    if (typeof speak === 'function') {
        const criticalCount = results.anomalies?.filter(a => a.severity === 'CRITICAL').length || 0;
        speak(`Neural engine analysis complete. ${criticalCount} critical anomalies detected. Document status: ${results.status}.`);
    }
}

// Export for dashboard use
window.runNeuralEngineAnalysis = runNeuralEngineAnalysis;
window.updateDashboardWithNeuralResults = updateDashboardWithNeuralResults;