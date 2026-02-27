import pandas as pd
import numpy as np

np.random.seed(42)

days = 365
dates = pd.date_range(start="2024-01-01", periods=days)

base_price = 30

# Time components
trend = np.linspace(0, 3, days)
weekly = 2 * np.sin(2 * np.pi * dates.dayofweek / 7)
yearly = 3 * np.sin(2 * np.pi * dates.dayofyear / 365)

# Supply
arrival_quantity = np.random.normal(500, 80, days)
inventory_level = np.random.normal(300, 50, days)
transport_delay_days = np.random.poisson(1, days)

# Weather
rainfall_mm = np.abs(np.random.normal(5, 3, days))
temperature_avg = np.random.normal(30, 5, days)
humidity = np.random.normal(70, 10, days)

# Market Cost
fuel_price = np.linspace(95, 105, days) + np.random.normal(0, 1, days)
cold_chain_temp = np.random.normal(4, 0.5, days)

# Demand
festival_flag = np.zeros(days)
festival_flag[100:105] = 1
festival_flag[250:255] = 1

urban_demand_index = np.random.normal(50, 10, days)

# --- Economic Logic ---
price = (
    base_price
    + trend
    + weekly
    + yearly
    - 0.01 * arrival_quantity
    - 0.005 * inventory_level
    + 0.03 * rainfall_mm
    + 0.2 * transport_delay_days
    + 0.15 * fuel_price
    + 0.05 * temperature_avg
    + 0.5 * festival_flag
    + np.random.normal(0, 1, days)
)

df = pd.DataFrame({
    "date": dates,
    "price": np.round(price, 2),
    "arrival_quantity": np.round(arrival_quantity, 2),
    "inventory_level": np.round(inventory_level, 2),
    "transport_delay_days": transport_delay_days,
    "rainfall_mm": np.round(rainfall_mm, 2),
    "temperature_avg": np.round(temperature_avg, 2),
    "humidity": np.round(humidity, 2),
    "fuel_price": np.round(fuel_price, 2),
    "cold_chain_temp": np.round(cold_chain_temp, 2),
    "festival_flag": festival_flag,
    "urban_demand_index": np.round(urban_demand_index, 2)
})

df.to_csv("agrichain_price_dataset.csv", index=False)

print("AGRICHAIN synthetic dataset generated.")