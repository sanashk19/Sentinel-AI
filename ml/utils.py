# ml/utils.py

import os
import cv2
import numpy as np

IMG_SIZE = 256

def load_data(base_path="ml_data"):
    X = []
    y = []

    # ORIGINAL → label 0
    for category in ["academic", "id", "employee"]:
        folder = f"{base_path}/original/{category}"

        for file in os.listdir(folder):
            path = os.path.join(folder, file)
            img = cv2.imread(path)

            if img is None:
                continue

            img = img / 255.0
            X.append(img)
            y.append(0)

    # FORGED → label 1
    for category in ["academic", "id", "employee"]:
        folder = f"{base_path}/forged/{category}"

        for file in os.listdir(folder):
            path = os.path.join(folder, file)
            img = cv2.imread(path)

            if img is None:
                continue

            img = img / 255.0
            X.append(img)
            y.append(1)

    X = np.array(X)
    y = np.array(y)

    print("Dataset Loaded:")
    print("X shape:", X.shape)
    print("y shape:", y.shape)

    return X, y