import joblib
import numpy as np
import os

MODEL_PATH = "saved_models/yield_model.pkl"


def estimate_yield(land_size, soil_quality, rainfall):

    if not os.path.exists(MODEL_PATH):
        raise Exception("Yield model not trained.")

    model = joblib.load(MODEL_PATH)

    sample_input = np.array([[land_size, soil_quality, rainfall]])
    prediction = model.predict(sample_input)[0]

    return round(prediction, 2)