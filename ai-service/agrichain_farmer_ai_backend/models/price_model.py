import os
import joblib
import numpy as np

# Absolute path to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "saved_models", "price_model.pkl")

model = None

if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    print("✅ Price model loaded successfully.")
else:
    print("⚠️ Price model file not found at:", MODEL_PATH)


def predict_price():
    if model is None:
        raise Exception("Price model not trained or not found.")

    # Dummy live inputs (can later replace with API inputs)
    demand_index = 75
    weekly_avg_price = 30
    volatility = 0.2

    X = np.array([[demand_index, weekly_avg_price, volatility]])

    predicted_price = model.predict(X)[0]

    return round(float(predicted_price), 2), weekly_avg_price