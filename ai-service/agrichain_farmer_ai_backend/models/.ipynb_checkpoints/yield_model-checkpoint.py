import joblib
import numpy as np

# Load trained model
model = joblib.load("models/yield_model.pkl")

def estimate_yield(land_size, rainfall, soil_quality, fertilizer, disease_severity):

    input_data = np.array([[land_size, rainfall, soil_quality, fertilizer, disease_severity]])
    prediction = model.predict(input_data)[0]

    return round(float(prediction), 2)