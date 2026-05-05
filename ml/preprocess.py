# ml/preprocess.py

import os
import cv2
import numpy as np

IMG_SIZE = 256

def process_folder(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    for root, dirs, files in os.walk(input_folder):
        for file in files:
            path = os.path.join(root, file)

            img = cv2.imread(path)

            # Skip invalid images
            if img is None:
                continue

            # Skip very small/broken images
            h, w = img.shape[:2]
            if h < 100 or w < 100:
                continue

            # Convert color (important)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Maintain aspect ratio
            scale = IMG_SIZE / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)

            img_resized = cv2.resize(img, (new_w, new_h))

            # Pad to square
            padded = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
            padded[:new_h, :new_w] = img_resized

            # Save as JPG (fix extension issues)
            filename = os.path.splitext(file)[0] + ".jpg"
            save_path = os.path.join(output_folder, filename)

            cv2.imwrite(save_path, cv2.cvtColor(padded, cv2.COLOR_RGB2BGR))


def prepare_dataset(base_path="Dataset"):
    print("🚀 Processing ORIGINAL dataset...")
    process_folder(f"{base_path}/Original/Academic", "ml_data/original/academic")
    process_folder(f"{base_path}/Original/Id_Kyc", "ml_data/original/id")
    process_folder(f"{base_path}/Original/Employee", "ml_data/original/employee")

    print("🚀 Processing FORGED dataset...")
    process_folder(f"{base_path}/Forged/F_Aacademic", "ml_data/forged/academic")  # match your folder name
    process_folder(f"{base_path}/Forged/F_Id_KYC", "ml_data/forged/id")
    process_folder(f"{base_path}/Forged/F_Employee", "ml_data/forged/employee")

    print("✅ Preprocessing completed!")


if __name__ == "__main__":
    prepare_dataset()