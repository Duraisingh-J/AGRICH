import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import joblib
import os

np.random.seed(42)

data = pd.DataFrame({
    "demand_index": np.random.randint(50, 100, 200),
    "weekly_avg_price": np.random.uniform(25, 35, 200),
    "volatility": np.random.uniform(0.1, 0.5, 200)
})

data["next_price"] = (
    data["weekly_avg_price"]
    + data["demand_index"] * 0.05
    - data["volatility"] * 10
)

X = data[["demand_index", "weekly_avg_price", "volatility"]]
y = data["next_price"]

model = LinearRegression()
model.fit(X, y)

os.makedirs("saved_models", exist_ok=True)
joblib.dump(model, "saved_models/price_model.pkl")

print("Price model trained and saved.")