import cv2
import numpy as np
import os

# Disable GPU for faster loading on CPU
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

import tensorflow as tf

IMG_SIZE = 256
model = None

# Try to load model with multiple compatibility approaches
def _load_model():
    global model
    
    # Approach 1: Try loading with legacy mode
    try:
        tf.keras.config.enable_unsafe_deserialization()
        model = tf.keras.models.load_model("ml/model.h5", compile=False)
        print("[ML Engine] Model loaded successfully (legacy mode)")
        return
    except Exception as e:
        print(f"[ML Engine] Legacy load failed: {str(e)[:100]}")
    
    # Approach 2: Try with custom object scope
    try:
        import keras
        with keras.utils.custom_object_scope({}):
            model = tf.keras.models.load_model("ml/model.h5", compile=False)
        print("[ML Engine] Model loaded successfully (custom scope)")
        return
    except Exception as e:
        print(f"[ML Engine] Custom scope load failed: {str(e)[:100]}")
    
    # Fallback: Model not available
    print("[ML Engine] Using fallback mode - ML scores will be neutral (0.5)")
    model = None

_load_model()

def preprocess_image(image_path):
    img = cv2.imread(image_path)

    if img is None:
        return None

    h, w = img.shape[:2]

    scale = IMG_SIZE / max(h, w)
    new_w = int(w * scale)
    new_h = int(h * scale)

    img = cv2.resize(img, (new_w, new_h))

    padded = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
    padded[:new_h, :new_w] = img

    img = padded / 255.0
    img = np.expand_dims(img, axis=0)

    return img


def analyze_ml(image_path):
    if model is None:
        print("[ML Engine] Model not loaded, returning default score")
        return {"ml_score": 0.5}
    
    img = preprocess_image(image_path)

    if img is None:
        return {"ml_score": 0.0}

    prediction = model.predict(img, verbose=0)[0][0]

    return {
        "ml_score": float(prediction)
    }

def get_model():
    return model