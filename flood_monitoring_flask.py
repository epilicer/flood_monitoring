from flask import Flask, render_template, request
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

app = Flask(__name__)

# API endpoint
API_URL = "https://environment.data.gov.uk/flood-monitoring/id/stations"

# Fetch available stations
def get_stations():
    response = requests.get(API_URL)
    if response.status_code == 200:
        data = response.json()
        stations = data['items']
        return pd.DataFrame([{ 'id': s['notation'], 'name': s['label'] } for s in stations])
    else:
        print("Failed to fetch stations.")
        return pd.DataFrame()

# Function to fetch stations
def fetch_stations():
    try:
        response = requests.get(API_URL, timeout=10)  # Set timeout to avoid hanging
        response.raise_for_status()
        return response.json().get("items", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching stations: {e}")  # Log error
        return []

# Fetch last 24-hour readings for a station
def get_readings(station_id):
    url = f"{API_URL}/{station_id}/readings?_sorted&_limit=50" # THIS IS NOT last 24h
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        readings = data['items']
        return pd.DataFrame([{ 'dateTime': r['dateTime'], 'value': r['value'] } for r in readings])
    else:
        print("Failed to fetch readings.")
        return pd.DataFrame()

https://environment.data.gov.uk/flood-monitoring/id/stations/4615TH/readings?_sorted&_limit=50
https://environment.data.gov.uk/flood-monitoring/id/stations/055003_TG_316/readings?_sorted&_limit=50

https://environment.data.gov.uk/flood-monitoring/id/stations/4615TH/readings?_sorted&_limit=1000&_since=1D
https://environment.data.gov.uk/flood-monitoring/id/stations/055003_TG_316/readings?_sorted&_limit=1000&_since=1D

# Main execution
stations_df = get_stations()
print(stations_df.to_string())
if not stations_df.empty:
    print(stations_df.head())  # Show first few stations
    station_id = stations_df.iloc[0]['id']  # Select first station for demo
    station_name = stations_df.iloc[0]['name']
    readings_df = get_readings(station_id)
    print(readings_df.head())  # Show first few readings

# Function to fetch stations
def fetch_stations():
    try:
        response = requests.get(API_URL, timeout=10)  # Set timeout to avoid hanging
        response.raise_for_status()
        return response.json().get("items", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching stations: {e}")  # Log error
        return []

def fetch_readings(station_id):
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        # Remove microseconds from ISO format
        since_time = start_time.replace(microsecond=0).isoformat()
        params = {"since": since_time, "_sorted": "true"}
        url = f"{API_URL}/{station_id}/readings"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        readings = response.json().get("items", [])
        return readings if readings else None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching readings for station {station_id}: {e}")
        return None

# Main execution
stations = fetch_stations()
for station in stations:
    station_id = station["stationReference"]
    print(station_id)
    readings = fetch_readings(station_id)
    print(readings)  # Show first few readings


# Function to fetch readings for a station
def fetch_readings_1(station_id):
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        params = {"since": start_time.isoformat(), "_sorted": "true"}
        url = f"{API_URL}/{station_id}/readings"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        readings = response.json().get("items", [])
        return readings if readings else []  # Return an empty list if no data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching readings for station {station_id}: {e}")
        return []

def fetch_readings_2(station_id):
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        params = {"since": start_time.isoformat(), "_sorted": "true"}
        url = f"{API_URL}/{station_id}/readings"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        readings = response.json().get("items", [])
        return readings if readings else None  # Return None if no data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching readings for station {station_id}: {e}")
        return None  # Return None to indicate failure

def fetch_readings(station_id):
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        # Remove microseconds from ISO format
        since_time = start_time.replace(microsecond=0).isoformat()
        params = {"since": since_time, "_sorted": "true"}
        url = f"{API_URL}/{station_id}/readings"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        readings = response.json().get("items", [])
        return readings if readings else None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching readings for station {station_id}: {e}")
        return None

import urllib.parse  # Add this at the top

def fetch_readings(station_id):
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        since_time = start_time.replace(microsecond=0).isoformat()
        params = {"since": since_time, "_sorted": "true"}
        # Encode the station ID to handle spaces and special characters
        encoded_station_id = urllib.parse.quote(station_id, safe="")
        url = f"{API_URL}/{encoded_station_id}/readings"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        readings = response.json().get("items", [])
        return readings if readings else None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching readings for station {station_id}: {e}")
        return None

# Function to fetch all stations' readings and compute average water levels
def compute_average_levels_1():
    stations = fetch_stations()
    station_data = []
    for station in stations:
        station_id = station["stationReference"]
        readings = fetch_readings(station_id)
        if readings:
            df = pd.DataFrame(readings)
            df["value"] = pd.to_numeric(df["value"], errors="coerce")  # Convert to numeric
            avg_level = df["value"].mean()  # Compute average
            if pd.notna(avg_level):
                station_data.append((station["label"], avg_level))
    # Sort by average water level
    station_data.sort(key=lambda x: x[1])
    return station_data[:3], station_data[-3:]  # Bottom 3 and Top 3 stations

def compute_average_levels():
    stations = fetch_stations()
    station_data = []    
    for station in stations:
        station_id = station["stationReference"]
        readings = fetch_readings(station_id)
        if readings is None:  # Skip stations that failed to fetch readings
            continue
        df = pd.DataFrame(readings)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")  # Convert to numeric
        avg_level = df["value"].mean()  # Compute average
        if pd.notna(avg_level):
            station_data.append((station["label"], avg_level))
    # Sort by average water level
    station_data.sort(key=lambda x: x[1])
    # Ensure there are enough stations before slicing
    return station_data[:3] if len(station_data) >= 3 else station_data, \
           station_data[-3:] if len(station_data) >= 3 else station_data


@app.template_filter("datetimeformat")
def datetimeformat(value):
    return value.strftime("%d-%b-%Y %H:%M:%S") if isinstance(value, pd.Timestamp) else value

# Home route
@app.route("/", methods=["GET", "POST"])
def home():
    stations = fetch_stations()
    if not stations:
        return "Failed to fetch stations."

    station_names = [station["label"] for station in stations]
    selected_station_name = request.form.get("station", station_names[0])

    # Get the selected station's ID
    selected_station = next(station for station in stations if station["label"] == selected_station_name)
    station_id = selected_station["stationReference"]

    # Fetch readings for the selected station
    readings = fetch_readings(station_id)
    if not readings:
        return "Failed to fetch readings."

    # Convert readings to a DataFrame
    df = pd.DataFrame(readings)
    df["dateTime"] = pd.to_datetime(df["dateTime"])
    df = df.sort_values(by="dateTime")

    # Create a Plotly graph
    if df.empty:
        graph_html = "<p>No data available for this station in the last 24 hours.</p>"
    else:
        fig = px.line(df, x="dateTime", y="value", title=f"Water Level Over Time for {selected_station_name}")
        graph_html = fig.to_html(full_html=False)

    # Prepare data for the table
    #table_data = df[["dateTime", "value"]].to_dict("records")

    # Get top and bottom 3 stations
    bottom_3, top_3 = compute_average_levels()

    return render_template(
        "index.html",
        stations=station_names,
        selected_station=selected_station_name,
        graph_html=graph_html,
        #table_data=table_data,
        top_3=top_3,
        bottom_3=bottom_3
    )

if __name__ == "__main__":
    app.run(debug=True)
