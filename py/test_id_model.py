from ultralytics import YOLO
import os

# Use the downloaded model from local path
model_path = "models/model.pt"

if not os.path.exists(model_path):
    print(f"Error: Model not found at {model_path}")
    print("Run 'python download_models.py' first to download the model.")
    exit(1)

print(f"Loading model from {model_path}...")
model = YOLO(model_path)

# Check for test images
test_images_dir = "test_images"
if not os.path.exists(test_images_dir):
    os.makedirs(test_images_dir)
    print(f"Created {test_images_dir} directory. Add your test images there.")
    print("Supported formats: .jpg, .jpeg, .png")
    
# Find any image in test_images
test_image = None
for f in os.listdir(test_images_dir):
    if f.lower().endswith(('.jpg', '.jpeg', '.png')):
        test_image = os.path.join(test_images_dir, f)
        break

if test_image:
    print(f"\nRunning inference on: {test_image}")
    results = model(test_image, save=True)
    
    # Print detection results
    for r in results:
        if r.boxes is not None and len(r.boxes) > 0:
            print(f"\nDetected {len(r.boxes)} object(s):")
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                label = model.names[cls_id]
                print(f"  - {label}: {conf:.2%} confidence")
        else:
            print("No objects detected in the image.")
    
    print(f"\nResults saved to: runs/detect/predict/")
else:
    print(f"\nNo test images found in {test_images_dir}/")
    print("Add an Aadhaar card image (jpg/jpeg/png) and run this script again.")
    print("\nAlternatively, test with any image path:")
    print('  results = model("path/to/your/image.jpg", save=True)')