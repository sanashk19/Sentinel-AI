from ultralytics import YOLO
from huggingface_hub import hf_hub_download
import os

# Create models directory if it doesn't exist
os.makedirs("./models", exist_ok=True)

# repo details
repo_config = dict(
    repo_id = "arnabdhar/YOLOv8-nano-aadhar-card",
    filename = "model.pt",
    local_dir = "./models"
)

print("Downloading Aadhaar YOLOv8 model from HuggingFace...")

# Download and load model
model_path = hf_hub_download(**repo_config)
model = YOLO(model_path)

# get id to label mapping
id2label = model.names
print("Model labels:", id2label)
print(f"Model saved to: {model_path}")
print("Download complete!")
