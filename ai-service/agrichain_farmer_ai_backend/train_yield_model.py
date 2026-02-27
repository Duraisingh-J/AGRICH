import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

np.random.seed(42)

data_size = 1000

data = pd.DataFrame({
    "land_size": np.random.uniform(1, 10, data_size),
    "rainfall": np.random.uniform(50, 200, data_size),
    "soil_quality": np.random.uniform(5, 10, data_size),
    "fertilizer": np.random.uniform(50, 200, data_size),
    "disease_severity": np.random.uniform(0, 1, data_size)
})

data["yield"] = (
    data["land_size"] *
    (data["rainfall"] * 0.3) *
    (data["soil_quality"] * 1.2) *
    (1 - data["disease_severity"]) *
    0.5
)

X = data.drop("yield", axis=1)
y = data["yield"]

model = RandomForestRegressor(n_estimators=100)
model.fit(X, y)

# Ensure models folder exists
os.makedirs("models", exist_ok=True)

joblib.dump(model, "models/yield_model.pkl")

print("Yield model trained and saved successfully.")