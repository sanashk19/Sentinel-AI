#!/usr/bin/env python3
"""
Download PAN Card Detection Model from HuggingFace
"""

import os
import torch

# Fix PyTorch 2.6+ weights_only security - allow ultralytics classes
try:
    from ultralytics.nn.tasks import DetectionModel
    torch.serialization.add_safe_globals([DetectionModel])
    print("Added DetectionModel to safe globals")
except ImportError:
    # If ultralytics not loaded yet, use unsafe load
    os.environ['TORCH_FORCE_WEIGHTS_ONLY_LOAD'] = '0'

from huggingface_hub import hf_hub_download
from ultralytics import YOLO

# Create models directory
os.makedirs("models", exist_ok=True)

print("Downloading PAN Card Detection Model from HuggingFace...")

try:
    # Download model
    model_path = hf_hub_download(
        repo_id="foduucom/pan-card-detection",
        filename="best.pt",
        local_dir="models"
    )
    
    # Rename to standard name
    final_path = "models/pan_card_model.pt"
    if model_path != final_path:
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(model_path, final_path)
    
    print(f"Model saved to: {final_path}")
    print("Download complete!")
    
    # Verify model loads
    model = YOLO(final_path)
    print(f"Model loaded successfully!")
    print(f"Model classes: {model.names}")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nTrying alternative loading method...")
    
    try:
        # Force load with weights_only=False
        import torch
        original_load = torch.load
        
        def patched_load(*args, **kwargs):
            kwargs['weights_only'] = False
            return original_load(*args, **kwargs)
        
        torch.load = patched_load
        
        model = YOLO(final_path)
        print(f"Model loaded successfully with patched loader!")
        print(f"Model classes: {model.names}")
        
        # Restore original
        torch.load = original_load
        
    except Exception as e2:
        print(f"Alternative loading also failed: {e2}")
        print("PAN validation will use text-based fallback detection")
