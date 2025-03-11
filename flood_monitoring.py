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


















import streamlit as st
import requests
import pandas as pd
#import matplotlib.pyplot as plt
import plotly.express as px
import folium
from streamlit_folium import folium_static
import time

# Base API URL
BASE_URL = "https://environment.data.gov.uk/flood-monitoring/id/stations"

# Fetch available stations
@st.cache_data
def get_stations():
    response = requests.get(BASE_URL)
    if response.status_code == 200:
        data = response.json()
        stations = data["items"]
        return pd.DataFrame([{ "id": s["notation"], "name": s["label"], "lat": s.get("lat"), "long": s.get("long"), "river": s.get("riverName", "Unknown") } for s in stations])
    else:
        st.error("Failed to fetch stations.")
        return pd.DataFrame()

# Fetch readings for a station with a time range
@st.cache_data
def get_readings(station_id, days):
    url = f"{BASE_URL}/{station_id}/readings?_sorted&_limit=1000&_since={days}D"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        readings = data["items"]
        return pd.DataFrame([{ "dateTime": r["dateTime"], "value": r["value"], "measure": r["measure"] } for r in readings])
    else:
        st.error("Failed to fetch readings.")
        return pd.DataFrame()

# Streamlit UI
st.title("Flood Monitoring Tool")

# Auto-refresh every 5 minutes
st_autorefresh = st.checkbox("Auto-refresh every 5 minutes", value=False)
if st_autorefresh:
    st.experimental_rerun()
    time.sleep(300)  # Refresh interval (5 minutes)

# Load stations data
stations_df = get_stations()

# Create a combobox (dropdown) for station selection
if not stations_df.empty:
    station_name = st.selectbox("Select a Station:", stations_df["name"])
    station_info = stations_df[stations_df["name"] == station_name].iloc[0]
    station_id = station_info["id"]
    st.write(f"**Selected Station ID:** {station_id}")
    st.write(f"**River:** {station_info['river']}")
    
    # Select historical data range
    days_option = st.selectbox("Select data range:", [1, 7, 30], index=0)
    readings_df = get_readings(station_id, days_option)

    if not readings_df.empty:
        readings_df["dateTime"] = pd.to_datetime(readings_df["dateTime"])
        readings_df = readings_df.sort_values("dateTime")
        
        # Separate water level and rainfall data if available
        water_levels = readings_df[readings_df["measure"].str.contains("level", na=False)]
        rainfall = readings_df[readings_df["measure"].str.contains("rainfall", na=False)]
        
        # Plot readings using Plotly with dual axes
        fig = px.line(water_levels, x="dateTime", y="value", markers=True,
                      title=f"Water Level & Rainfall for {station_name}",
                      labels={"dateTime": "Time", "value": "Water Level (m)"})
        
        if not rainfall.empty:
            fig.add_scatter(x=rainfall["dateTime"], y=rainfall["value"], mode='lines+markers', name='Rainfall (mm)')
        
        st.plotly_chart(fig)
    else:
        st.warning("No readings available for this station.")

    # Fetch and display readings
    #readings_df = get_readings(station_id)
    #if not readings_df.empty:
    #    readings_df["dateTime"] = pd.to_datetime(readings_df["dateTime"])
    #    readings_df = readings_df.sort_values("dateTime")
        # Plot readings
        #fig, ax = plt.subplots(figsize=(10, 5))
        #ax.plot(readings_df["dateTime"], readings_df["value"], marker='o', linestyle='-')
        #ax.set_xlabel("Time")
        #ax.set_ylabel("Water Level (m)")
        #ax.set_title(f"Water Level Readings for {station_name}")
        #ax.tick_params(axis='x', rotation=45)
        #ax.grid()
        #st.pyplot(fig)
    #    # Plot readings using Plotly
    #    fig = px.line(readings_df, x="dateTime", y="value", markers=True,
    #                  title=f"Water Level Readings for {station_name}",
    #                  labels={"dateTime": "Time", "value": "Water Level (m)"})
    #    st.plotly_chart(fig)
    #else:
    #    st.warning("No readings available for this station.")

    # Display map with station location
    if not pd.isna(station_info["lat"]) and not pd.isna(station_info["long"]):
        st.write("### Station Location")
        station_map = folium.Map(location=[station_info["lat"], station_info["long"]], zoom_start=12)
        folium.Marker(
            [station_info["lat"], station_info["long"]],
            popup=f"{station_name}<br>River: {station_info['river']}<br>ID: {station_id}",
            tooltip=station_name
        ).add_to(station_map)
        folium_static(station_map)

else:
    st.warning("No stations available.")