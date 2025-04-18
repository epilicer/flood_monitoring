"""
Aim: UK Flood Monitoring Dashboard

Dependencies: pandas, plotly, requests, Flask

Usage: python flask_app.py
"""

from flask import Flask, render_template, request, jsonify
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
		 
app = Flask(__name__)

API_URL = "https://environment.data.gov.uk/flood-monitoring/id/stations"

# Cache station data for 1 hour
stations_cache = None  
last_updated = 0  
CACHE_DURATION = 3600  

# Fetch available stations with caching
def get_stations():
    global stations_cache, last_updated
    current_time = datetime.now().timestamp()
    
    if stations_cache is None or (current_time - last_updated > CACHE_DURATION):
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            stations = data["items"]
            stations_cache = pd.DataFrame([{ "id": s["notation"], "name": s["label"] } for s in stations])
            last_updated = current_time  
        else:
            print("Failed to fetch stations.")
            stations_cache = pd.DataFrame()
    
    return stations_cache

# Fetch readings for a selected station and time range
def get_readings(station_id, days=1):
    # Calculate the start time based on the number of days
    start_time = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"{API_URL}/{station_id}/readings?since={start_time}&_sorted=true"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        readings = data['items']
        
        if readings:
            return pd.DataFrame([{ 
                "dateTime": r["dateTime"], 
                "value": r["value"] 
            } for r in readings])
    return pd.DataFrame()  # Return empty DataFrame if no data

@app.route("/")
def home():
    stations_df = get_stations()
    stations_list = stations_df.to_dict("records")  
    return render_template("index.html", stations=stations_list)

@app.route("/get_graph", methods=["POST"])
def get_graph():
    station_id = request.json.get("station_id")
    selected_station_name = request.json.get("station_name", "Unknown Station")
    days = int(request.json.get("time_range", 1))  # Default to 1 day if not specified
    
    # Validate station_id
    if not station_id:
        return jsonify({"graph": "<p class='error-message'>Invalid station ID provided.</p>"}), 400
    
    # Check if station exists in our cache
    stations_df = get_stations()
    if not stations_df.empty and station_id not in stations_df['id'].values:
        return jsonify({"graph": "<p class='error-message'>Station not found.</p>"}), 404
    
    readings = get_readings(station_id, days)
    
    if readings.empty:
        return jsonify({"graph": f"<p>No data available for this station in the last {days} day(s).</p>"})

    readings["dateTime"] = pd.to_datetime(readings["dateTime"])
    readings = readings.sort_values(by="dateTime")

    # Create the Plotly graph with better date formatting
    fig = px.line(readings, x="dateTime", y="value", title=f"Water Level Over {days} Day(s) for {selected_station_name}")
    
    # Adjust the tick format based on the time range
    tick_format = "%d-%b %H:%M" if days <= 3 else "%d-%b"
    
    fig.update_xaxes(
        title_text="Date & Time",
        tickformat=tick_format,
        tickangle=-45,
        nticks=10 if days <= 3 else 7
    )
    fig.update_yaxes(title_text="Water Level (m)")
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified"
    )
    graph_html = fig.to_html(full_html=False)

    return jsonify({"graph": graph_html})

@app.route("/refresh_cache", methods=["POST"])
def refresh_cache():
    global stations_cache, last_updated
    stations_cache = None
    last_updated = 0
    
    # Trigger a refresh
    stations = get_stations()
    
    return jsonify({
        "success": True, 
        "message": "Cache refreshed successfully",
        "stations_count": len(stations)
    })

if __name__ == "__main__":
    app.run(debug=True)
