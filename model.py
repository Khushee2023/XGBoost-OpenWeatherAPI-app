import xgboost as xgb


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


model = xgb.XGBRegressor()
model.load_model("model.pkl")

def predict_energy_demand(X):

    return model.predict(X)
