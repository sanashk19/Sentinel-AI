# ml/train.py

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from utils import load_data

IMG_SIZE = 256

def create_model():
    model = Sequential([
        Conv2D(32, (3,3), activation='relu', input_shape=(IMG_SIZE, IMG_SIZE, 3)),
        MaxPooling2D(),

        Conv2D(64, (3,3), activation='relu'),
        MaxPooling2D(),

        Flatten(),
        Dense(64, activation='relu'),
        Dense(1, activation='sigmoid')
    ])

    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy']
    )

    return model


def train():
    X, y = load_data()

    model = create_model()

    model.fit(X, y, epochs=5, batch_size=16)

    model.save("ml/model.h5")
    print("✅ Model saved as ml/model.h5")


if __name__ == "__main__":
    train()