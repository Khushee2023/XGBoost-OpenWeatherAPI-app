# routes.py
from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from model import model, FEATURES, predict_energy_demand
import matplotlib
matplotlib.use('Agg')

OPENWEATHER_API_KEY = "12345677"

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

def get_coordinates(location):
   
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": location, "appid": OPENWEATHER_API_KEY, "units": "metric"}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["coord"]["lat"], data["coord"]["lon"]
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error fetching coordinates: {str(e)}")

def get_daily_forecast(lat, lon):
   
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"lat": lat, "lon": lon, "units": "metric", "appid": OPENWEATHER_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        forecasts = data.get("list", [])
        # Filter entries with "18:00:00" in dt_txt
        daily_forecasts = [f for f in forecasts if "18:00:00" in f.get("dt_txt", "")]
        return daily_forecasts[:5]
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error fetching forecast: {str(e)}")

def get_hourly_forecast(lat, lon):
    
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"lat": lat, "lon": lon, "units": "metric", "appid": OPENWEATHER_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        forecasts = data.get("list", [])
        return forecasts
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error fetching hourly forecast: {str(e)}")

def month_to_season(month):
    return {12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3}[month]

def prepare_forecast_features(forecasts):
  
    rows = []
    for forecast in forecasts:
        dt = datetime.fromtimestamp(forecast["dt"])
        rows.append({
            "timestamp": dt,
            "year": dt.year,
            "month": dt.month,
            "day": dt.day,
            "hour": dt.hour,
            "day_of_week": dt.weekday(),
            "season": month_to_season(dt.month),
            "temperature": forecast["main"]["temp"],
            "feels_like": forecast["main"]["feels_like"],
            "humidity": forecast["main"]["humidity"],
            "pressure": forecast["main"]["pressure"],
            "wind_speed": forecast["wind"]["speed"],
            "wind_direction": forecast["wind"]["deg"],
            "cloud_coverage": forecast["clouds"]["all"],
            "precipitation": forecast.get("rain", {}).get("3h", 0)
        })
    return pd.DataFrame(rows)

def generate_plot(df_forecast, predictions):
    """Generate and encode a plot for visualization of daily forecast."""
    plt.figure(figsize=(10, 6))
    plt.plot(df_forecast["timestamp"], predictions, marker='o', linestyle='-')
    plt.title("Predicted Energy Demand for Next 5 Days")
    plt.xlabel("Date")
    plt.ylabel("Predicted Energy Demand")
    plt.grid(True)
    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return plot_url

@bp.route('/predict', methods=["POST"])
def predict_route():
    try:
        data = request.get_json()
        user_timestamp_str, location = data.get("timestamp"), data.get("location")
        if not user_timestamp_str or not location:
            return jsonify({"error": "Both 'timestamp' and 'location' are required."}), 400
        
        datetime.fromisoformat(user_timestamp_str)  # Validate timestamp
        lat, lon = get_coordinates(location)
        daily_forecasts = get_daily_forecast(lat, lon)
        df_features = prepare_forecast_features(daily_forecasts)
        X_future = df_features[FEATURES]
        predictions = predict_energy_demand(X_future)
        df_features["predicted_energy_demand"] = predictions
        plot_image = generate_plot(df_features, predictions)
        
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        tomorrow_row = df_features[df_features["timestamp"].dt.date == tomorrow]
        message = (f"{location}'s peak demand tomorrow: {tomorrow_row['predicted_energy_demand'].values[0]:.0f} MW at 6 PM."
                   if not tomorrow_row.empty else "Tomorrow's forecast data is unavailable.")
        
        return jsonify({"message": message, "plot_image": plot_image})
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@bp.route('/predict_hourly', methods=["POST"])
def predict_hourly_route():
    try:
        data = request.get_json()
        user_timestamp_str, location = data.get("timestamp"), data.get("location")
        if not user_timestamp_str or not location:
            return jsonify({"error": "Both 'timestamp' and 'location' are required."}), 400
        
        datetime.fromisoformat(user_timestamp_str)  # Validate timestamp
        lat, lon = get_coordinates(location)
        hourly_forecasts = get_hourly_forecast(lat, lon)
        df_features = prepare_forecast_features(hourly_forecasts)
        X_future = df_features[FEATURES]
        predictions = predict_energy_demand(X_future)
        df_features["predicted_energy_demand"] = predictions
        
        # Prepare a list of forecast items (all hourly entries)
        forecast_list = []
        # Group by day for easier display:
        grouped = df_features.groupby(df_features["timestamp"].dt.date)
        for date, group in grouped:
            day_forecasts = []
            for _, row in group.iterrows():
                day_forecasts.append({
                    "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "predicted_energy_demand": float(row["predicted_energy_demand"]),
                    "temperature": row["temperature"],
                    "humidity": row["humidity"]
                })
            forecast_list.append({
                "date": str(date),
                "forecasts": day_forecasts
            })
        
        return jsonify({"forecasts": forecast_list})
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
