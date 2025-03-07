import streamlit as st
import requests
import pandas as pd

# Base API URL
BASE_URL = "https://environment.data.gov.uk/flood-monitoring/id/stations"

# Fetch available stations
@st.cache_data
def get_stations():
    response = requests.get(BASE_URL)
    if response.status_code == 200:
        data = response.json()
        stations = data["items"]
        return pd.DataFrame([{ "id": s["notation"], "name": s["label"] } for s in stations])
    else:
        st.error("Failed to fetch stations.")
        return pd.DataFrame()

# Streamlit UI
st.title("Flood Monitoring Tool")

# Load stations data
stations_df = get_stations()

# Create a combobox (dropdown) for station selection
if not stations_df.empty:
    station_name = st.selectbox("Select a Station:", stations_df["name"])
    station_id = stations_df[stations_df["name"] == station_name]["id"].values[0]
    st.write(f"Selected Station ID: {station_id}")
else:
    st.warning("No stations available.")

