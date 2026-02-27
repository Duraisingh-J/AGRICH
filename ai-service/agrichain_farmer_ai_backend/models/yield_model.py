import joblib
import numpy as np
import os

# Load trained model
model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "yield_model.pkl"))
model = joblib.load(model_path)

def estimate_yield(land_size, rainfall, soil_quality, fertilizer, disease_severity):

    input_data = np.array([[land_size, rainfall, soil_quality, fertilizer, disease_severity]])
    prediction = model.predict(input_data)[0]

    return round(float(prediction), 2)