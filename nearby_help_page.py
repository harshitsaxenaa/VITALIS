import streamlit as st
import json
import time

ACCIDENT_DB = 'logs/severity_log.json'

st.title("🚨 Accident Alert for Nearby Helpers / Clinics")
try:
    with open(ACCIDENT_DB, 'r') as f:
        data = json.load(f)
        if data:
            latest = data[-1]  # Get the most recent entry
        else:
            st.warning("No recent accident data available.")
            st.stop()
except:
    st.error("Error loading accident data.")
    st.stop()

# Display info
st.subheader("⚠️ Accident Detected Nearby")
st.write(f"**Date & Time:** {latest['start_time']}")
st.write(f"**Location:** ABC")  # Hardcoded for now
st.write(f"**Severity Score:** {latest['severity_score']}")
st.info("If you're a nearby clinic or passerby, kindly proceed to the location for first aid or assistance.")
