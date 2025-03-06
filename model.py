# model.py
import xgboost as xgb

# Define the feature order expected by the model
FEATURES = [
    'hour', 
    'day_of_week', 
    'day', 
    'month', 
    'year', 
    'season',
    'temperature', 
    'feels_like', 
    'humidity', 
    'pressure',
    'wind_speed', 
    'wind_direction', 
    'cloud_coverage', 
    'precipitation'
]

# Load the pre-trained XGBoost model.
# Ensure that "model.pkl" (or "model.xgb") is in your project directory.
model = xgb.XGBRegressor()
model.load_model("model.pkl")

def predict_energy_demand(X):
    """Predict energy demand for a given feature DataFrame X."""
    return model.predict(X)
