import numpy as np
from sklearn.linear_model import LinearRegression
import joblib
import os

np.random.seed(42)

land = np.random.uniform(1, 5, 200)
soil = np.random.uniform(60, 100, 200)
rain = np.random.uniform(5, 15, 200)

yield_output = land * soil * rain * 0.1

X = np.column_stack((land, soil, rain))
y = yield_output

model = LinearRegression()
model.fit(X, y)

os.makedirs("saved_models", exist_ok=True)
joblib.dump(model, "saved_models/yield_model.pkl")

print("Yield model trained and saved.")