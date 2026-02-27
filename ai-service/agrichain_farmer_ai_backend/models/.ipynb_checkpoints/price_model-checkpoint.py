import pandas as pd
from prophet import Prophet
import numpy as np

# Simulated historical data
def generate_sample_data():
    dates = pd.date_range(start="2024-01-01", periods=60)
    prices = np.random.normal(loc=30, scale=2, size=60)
    return pd.DataFrame({"ds": dates, "y": prices})


def predict_price():
    try:
        df = generate_sample_data()

        model = Prophet()
        model.fit(df)

        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)

        next_price = forecast.iloc[-1]["yhat"]
        return round(float(next_price), 2)

    except Exception as e:
        print("Price prediction error:", e)
        return 30.0  # fallback safe value


def get_7day_average():
    try:
        df = generate_sample_data()
        return round(float(df["y"].tail(7).mean()), 2)

    except:
        return 29.0