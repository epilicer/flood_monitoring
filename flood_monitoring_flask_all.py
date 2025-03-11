from flask import Flask, render_template, request, jsonify
import requests
import pandas as pd
import plotly.express as px

app = Flask(__name__)

# API endpoint
API_URL = "https://environment.data.gov.uk/flood-monitoring/id/stations"

# Function to fetch all stations
def get_stations():
    response = requests.get(API_URL)
    if response.status_code == 200:
        data = response.json()
        stations = [
            {
                "id": s["@id"].split("/")[-1],
                "name": s["label"],
                "lat": s.get("lat"),
                "long": s.get("long"),
                "river": s.get("riverName", "Unknown")
            }
            for s in data["items"]
        ]
        return pd.DataFrame(stations)
    return pd.DataFrame()

stations_df = get_stations()

def get_latest_readings_all():
    station_data = []
    count = 0  # Track progress
    for station_id in stations_df["id"]:
        count += 1
        print(f"Fetching data for station {count}/{len(stations_df)}: {station_id}")  # Track requests        
        url = f"{API_URL}/{station_id}/readings?_sorted&_limit=1"
        #url = f"{API_URL}/{station_id}/readings?_sorted&_limit=50"
        #url = f"{API_URL}/{station_id}/readings?_sorted&_limit=1000&_since=1D"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                latest_reading = data["items"][0]
                station_data.append({
                    "id": station_id,
                    "value": latest_reading["value"],
                    "dateTime": latest_reading["dateTime"]
                })
    print(f"Total stations processed: {len(station_data)}")
    return pd.DataFrame(station_data)

def get_latest_readings():
    url = "https://environment.data.gov.uk/flood-monitoring/id/measures"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        measures = data["items"]
        station_data = [
            {
                "id": m["stationReference"],
                "value": m["latestReading"]["value"] if "latestReading" in m else None,
                "dateTime": m["latestReading"]["dateTime"] if "latestReading" in m else None
            }
            for m in measures if "latestReading" in m
        ]
        return pd.DataFrame(station_data)
    return pd.DataFrame()

@app.route("/")
def home():
    # Fetch updated readings
    readings_df = get_latest_readings()
    
    # Merge with station data
    stations_with_readings = stations_df.merge(readings_df, on="id", how="left")

    # Create a Plotly choropleth map
    fig = px.choropleth(
        stations_with_readings,
        locations="id",
        color="value",
        locationmode="ISO-3",
        color_continuous_scale="Blues",
        scope="europe",
        labels={'value': 'Water Level'}
    )
    map_html = fig.to_html(full_html=False)

    return render_template("index.html", stations=stations_with_readings.to_dict(orient="records"), map_html=map_html)

if __name__ == "__main__":
    app.run(debug=True)
