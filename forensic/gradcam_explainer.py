#!/usr/bin/env python3

import os
from pathlib import Path

import cv2
import numpy as np


def _iter_layers(model):
    try:
        layers = list(getattr(model, "layers", []) or [])
    except Exception:
        layers = []

    for layer in layers:
        yield layer
        try:
            sublayers = list(getattr(layer, "layers", []) or [])
        except Exception:
            sublayers = []
        for sub in sublayers:
            yield sub


def _find_last_conv_layer(model):
    try:
        import tensorflow as tf

        conv_layers = [l for l in _iter_layers(model) if isinstance(l, tf.keras.layers.Conv2D)]
        for layer in reversed(conv_layers):
            try:
                out_shape = getattr(layer, "output_shape", None)
                if out_shape is not None and len(out_shape) == 4:
                    return layer
            except Exception:
                continue
        return conv_layers[-1] if conv_layers else None
    except Exception:
        return None


def generate_gradcam(image_path: str, model) -> str:
    """Generate Grad-CAM overlay image and save it under outputs/.

    Args:
        image_path: Path to input image
        model: Loaded tf.keras model

    Returns:
        Path to saved overlay image (string). Empty string on failure.
    """

    try:
        import tensorflow as tf

        if model is None:
            return ""

        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            return ""

        input_shape = getattr(model, "input_shape", None)
        if not input_shape or len(input_shape) != 4:
            return ""

        target_h = int(input_shape[1])
        target_w = int(input_shape[2])
        if not target_h or not target_w:
            return ""

        orig_h, orig_w = img_bgr.shape[:2]

        img_resized = cv2.resize(img_bgr, (target_w, target_h))
        x = img_resized.astype(np.float32) / 255.0
        x = np.expand_dims(x, axis=0)

        last_conv_layer = _find_last_conv_layer(model)
        if last_conv_layer is None:
            return ""

        grad_model = tf.keras.models.Model([model.inputs], [last_conv_layer.output, model.output])

        with tf.GradientTape() as tape:
            conv_outputs, predictions = grad_model(x)

            if len(predictions.shape) == 2 and predictions.shape[-1] > 1:
                class_idx = tf.argmax(predictions[0])
                loss = predictions[:, class_idx]
            else:
                loss = predictions[:, 0]

        grads = tape.gradient(loss, conv_outputs)
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

        conv_outputs = conv_outputs[0]
        heatmap = tf.reduce_sum(conv_outputs * pooled_grads, axis=-1)
        heatmap = tf.nn.relu(heatmap)
        heatmap = heatmap / (tf.reduce_max(heatmap) + 1e-10)

        heatmap = heatmap.numpy()
        heatmap = cv2.resize(heatmap, (orig_w, orig_h), interpolation=cv2.INTER_CUBIC)

        heatmap = np.clip(heatmap, 0.0, 1.0)
        if float(np.max(heatmap)) > 0:
            heatmap = heatmap / (float(np.max(heatmap)) + 1e-10)

        thresh = 0.6
        mask = (heatmap >= thresh).astype(np.uint8) * 255

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        overlay = img_bgr.copy()

        red_layer = np.zeros_like(img_bgr)
        red_layer[:, :, 2] = 255

        mask_f = (mask.astype(np.float32) / 255.0)
        alpha = (mask_f * 0.55).astype(np.float32)
        alpha = cv2.GaussianBlur(alpha, (0, 0), sigmaX=15, sigmaY=15)
        alpha = np.clip(alpha, 0.0, 0.65)

        overlay = (overlay.astype(np.float32) * (1.0 - alpha[:, :, None]) + red_layer.astype(np.float32) * alpha[:, :, None]).astype(np.uint8)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 300:
                continue
            (x_c, y_c), radius = cv2.minEnclosingCircle(cnt)
            center = (int(x_c), int(y_c))
            r = max(12, int(radius))
            cv2.circle(overlay, center, r, (0, 0, 255), thickness=4)

        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)

        base = Path(image_path).stem
        out_path = output_dir / f"{base}_gradcam.png"
        cv2.imwrite(str(out_path), overlay)

        print("[GradCAM] Generated:", str(out_path))
        return str(out_path)

    except Exception as e:
        print("[GradCAM] Error generating Grad-CAM:", repr(e))
        return ""
