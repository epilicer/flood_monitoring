import requests
import pandas as pd
import matplotlib.pyplot as plt

# Base API URL
BASE_URL = "https://environment.data.gov.uk/flood-monitoring/id/stations"

# Fetch available stations
def get_stations():
    response = requests.get(BASE_URL)
    if response.status_code == 200:
        data = response.json()
        stations = data['items']
        return pd.DataFrame([{ 'id': s['notation'], 'name': s['label'] } for s in stations])
    else:
        print("Failed to fetch stations.")
        return pd.DataFrame()

# Fetch last 24-hour readings for a station
def get_readings(station_id):
    url = f"{BASE_URL}/{station_id}/readings?_sorted&_limit=50"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        readings = data['items']
        return pd.DataFrame([{ 'dateTime': r['dateTime'], 'value': r['value'] } for r in readings])
    else:
        print("Failed to fetch readings.")
        return pd.DataFrame()

# Plot readings
def plot_readings(df, station_name):
    if df.empty:
        print("No data available to plot.")
        return
    df['dateTime'] = pd.to_datetime(df['dateTime'])
    df = df.sort_values('dateTime')
    
    plt.figure(figsize=(10, 5))
    plt.plot(df['dateTime'], df['value'], marker='o', linestyle='-')
    plt.xlabel("Time")
    plt.ylabel("Water Level (m)")
    plt.title(f"Water Level Readings for {station_name}")
    plt.xticks(rotation=45)
    plt.grid()
    plt.show()

# Main execution
stations_df = get_stations()
if not stations_df.empty:
    print(stations_df.head())  # Show first few stations
    station_id = stations_df.iloc[0]['id']  # Select first station for demo
    station_name = stations_df.iloc[0]['name']
    readings_df = get_readings(station_id)
    print(readings_df.head())  # Show first few readings
    plot_readings(readings_df, station_name)
