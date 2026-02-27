import os
import joblib
import numpy as np

# Absolute project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "saved_models", "yield_model.pkl")

model = None

if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    print("✅ Yield model loaded successfully.")
else:
    print("⚠️ Yield model file not found at:", MODEL_PATH)


def estimate_yield(land_size, soil_quality, rainfall):

    if model is None:
        raise Exception("Yield model not trained or not found.")

    sample_input = np.array([[land_size, soil_quality, rainfall]])
    prediction = model.predict(sample_input)[0]

    return round(float(prediction), 2)