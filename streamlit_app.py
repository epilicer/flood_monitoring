'''
streamlit run streamlit_app.py
'''
"""
Aim: UK Flood Monitoring Dashboard

Dependencies: pandas, plotly, requests, streamlit

Usage: streamlit run streamlit_app.py
"""

# Import libraries
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import folium_static

# Base API URL
API_URL = "https://environment.data.gov.uk/flood-monitoring/id/stations"

# Fetch available stations
@st.cache_data
def get_stations():
    response = requests.get(API_URL)
    if response.status_code == 200:
        data = response.json()
        stations = data["items"]
        return pd.DataFrame([{ "id": s["notation"], "name": s["label"], "lat": s.get("lat"), "long": s.get("long"), "river": s.get("riverName", "Unknown") } for s in stations])
    else:
        st.error("Failed to fetch stations.")
        return pd.DataFrame()

# Fetch last 24h readings for a station
@st.cache_data
def get_readings(station_id):
    url = f"{API_URL}/{station_id}/readings?_sorted&_limit=1000&_since=1D" # f"{API_URL}/{station_id}/readings?_sorted&_limit=50"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        readings = data["items"]
        return pd.DataFrame([{ "dateTime": r["dateTime"], "value": r["value"] } for r in readings])
    else:
        st.error("Failed to fetch readings.")
        return pd.DataFrame()

# Streamlit Layout
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

# Streamlit UI
#st.title("Flood Monitoring Tool")
st.sidebar.title("Station Selection")

# Load stations data
stations_df = get_stations()

# Create a combobox (dropdown) for station selection
if not stations_df.empty:
    #station_name = st.selectbox("Select a Station:", stations_df["name"])
    station_name = st.sidebar.selectbox("Select a Station:", stations_df["name"], index=0)
    station_info = stations_df[stations_df["name"] == station_name].iloc[0]
    station_id = station_info["id"]
    st.write(f"**Selected Station ID:** {station_id}")
    st.write(f"**River:** {station_info['river']}")

    # Fetch and display readings
    readings_df = get_readings(station_id)
    if not readings_df.empty:
        readings_df["dateTime"] = pd.to_datetime(readings_df["dateTime"])
        readings_df = readings_df.sort_values("dateTime")
        # Plot readings using Plotly
        fig = px.line(readings_df, x="dateTime", y="value", markers=True,
                      title=f"Water Level Readings for {station_name}",
                      labels={"dateTime": "Time", "value": "Water Level (m)"})
        st.subheader("Last 24 Hours Water Level")
        st.plotly_chart(fig)

    else:
        st.warning("No readings available for this station.")

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