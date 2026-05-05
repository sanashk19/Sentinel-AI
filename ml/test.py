# ml/test.py

import cv2
import numpy as np
import tensorflow as tf

IMG_SIZE = 256

model = tf.keras.models.load_model("ml/model.h5")

def predict(image_path):
    img = cv2.imread(image_path)
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    img = img / 255.0

    img = np.expand_dims(img, axis=0)

    prediction = model.predict(img)[0][0]

    print("Forgery Probability:", prediction)

    if prediction > 0.5:
        print("⚠️ Likely FORGED")
    else:
        print("✅ Likely ORIGINAL")


predict(r"C:\Users\91951\OneDrive\Desktop\senitel ai\ml_data\original\id\Aadhaar_2 (1).jpg")  # put any image