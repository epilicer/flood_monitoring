'''
streamlit run streamlit_app.py
'''

# Import libraries
import streamlit as st
import requests
import pandas as pd
#import matplotlib.pyplot as plt
import plotly.express as px
import folium
from streamlit_folium import folium_static
from folium.plugins import HeatMap
import altair as alt
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

# Fetch last 24h readings for a station
@st.cache_data
def get_readings(station_id):
    url = f"{BASE_URL}/{station_id}/readings?_sorted&_limit=1000&_since=1D" # f"{BASE_URL}/{station_id}/readings?_sorted&_limit=50"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        readings = data["items"]
        return pd.DataFrame([{ "dateTime": r["dateTime"], "value": r["value"] } for r in readings])
    else:
        st.error("Failed to fetch readings.")
        return pd.DataFrame()

# Get all data
@st.cache_data
def get_all_readings():
    station_data = []
    for station_id in stations_df["id"]:
        url = f"{BASE_URL}/{station_id}/readings?_sorted&_limit=1"
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
    return pd.DataFrame(station_data)

# Display the map of last 24h readings
def make_choropleth(input_df, input_id, input_column, input_color_theme):
    choropleth = px.choropleth(
        input_df,
        locations=input_id,  # This could be station IDs or regions
        color=input_column,  # Water level readings
        locationmode="ISO-3",  # Use appropriate geographic mapping
        color_continuous_scale=input_color_theme,
        range_color=(input_df[input_column].min(), input_df[input_column].max()),
        scope="europe",  # Focus on the UK
        labels={'value': 'Water Level'}
    )
    choropleth.update_traces(
        hovertemplate="<b>Station:</b> %{customdata[0]}<br>"
                      "<b>Water Level:</b> %{z}m<br>"
                      "<b>Time:</b> %{customdata[1]}"
    )
    choropleth.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350
    )
    return choropleth

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

    # Map with Heatmap
    st.subheader("Flood Monitoring Stations - Heatmap")
    station_map = folium.Map(location=[52.5, -1.5], zoom_start=6)
    #heat_data = [[row["lat"], row["long"]] for _, row in stations_df.dropna(subset=["lat", "long"]).iterrows()]
    #heat_data = [
    #    [float(row["lat"]), float(row["long"])]
    #    for _, row in stations_df.iterrows()
    #    if pd.notna(row["lat"]) and pd.notna(row["long"])
    #    and isinstance(row["lat"], (int, float)) and isinstance(row["long"], (int, float))
    #]
    heat_data = []
    for _, row in stations_df.iterrows():
        try:
            lat = float(row["lat"])
            lon = float(row["long"])
            heat_data.append([lat, lon])
        except (ValueError, TypeError):
            continue  # Skip invalid data
    HeatMap(heat_data).add_to(station_map)
    folium_static(station_map)

    # Fetch and display readings
    readings_df = get_readings(station_id)
    if not readings_df.empty:
        readings_df["dateTime"] = pd.to_datetime(readings_df["dateTime"])
        readings_df = readings_df.sort_values("dateTime")
        
        # Plot readings
        #fig, ax = plt.subplots(figsize=(10, 5))
        #ax.plot(readings_df["dateTime"], readings_df["value"], marker='o', linestyle='-')
        #ax.set_xlabel("Time")
        #ax.set_ylabel("Water Level (m)")
        #ax.set_title(f"Water Level Readings for {station_name}")
        #ax.tick_params(axis='x', rotation=45)
        #ax.grid()
        #st.pyplot(fig)

        # Plot readings using Plotly
        fig = px.line(readings_df, x="dateTime", y="value", markers=True,
                      title=f"Water Level Readings for {station_name}",
                      labels={"dateTime": "Time", "value": "Water Level (m)"})
        
        st.subheader("Last 24 Hours Water Level")
        st.plotly_chart(fig)


        all_readings_df = get_all_readings()
        stations_with_readings = stations_df.merge(all_readings_df, on="id", how="left")

        # Prepare Data for Choropleth
        latest_readings = readings_df.groupby("id").last().reset_index()  # Latest value per station
        latest_readings["region"] = "GB"  # Placeholder, adjust with real region data if available

        # Create Choropleth Map
        choropleth_fig = make_choropleth(
            latest_readings,
            input_id="region",  # Change this if regions are available
            input_column="value",
            input_color_theme="Blues"
        )

        st.plotly_chart(choropleth_fig)


    else:
        st.warning("No readings available for this station.")

    # Display map with station location
    #if not pd.isna(station_info["lat"]) and not pd.isna(station_info["long"]):
    #    st.write("### Station Location")
    #    station_map = folium.Map(location=[station_info["lat"], station_info["long"]], zoom_start=12)
    #    folium.Marker(
    #        [station_info["lat"], station_info["long"]],
    #        popup=f"{station_name}<br>River: {station_info['river']}<br>ID: {station_id}",
    #        tooltip=station_name
    #    ).add_to(station_map)    
    #    folium_static(station_map)

else:
    st.warning("No stations available.")