# Streamlit ILP – Individual Launch Point Berechnung
import streamlit as st
import utm
import numpy as np
import pandas as pd
import math

st.set_page_config(page_title="ILP – Individual Launch Point")

st.title("ILP – Individual Launch Point")

# --- Eingaben ---
zone = st.selectbox("UTM-Zone", ["32T", "33T", "34T"], index=1)
zone_number = int(zone[:-1])
zone_letter = zone[-1]

format = st.selectbox("Koordinatenformat", ["4/4", "5/4"])

easting = st.number_input("UTM-Ostwert", value=654200)
northing = st.number_input("UTM-Nordwert", value=5231170)

lat, lon = utm.to_latlon(easting, northing, zone_number, zone_letter)
st.caption(f"WGS84 (nur intern): {lat:.6f}, {lon:.6f}")

range_km = st.slider("Erlaubte Startdistanz vom Ziel (km)", 1, 50, (2, 10))

height_min, height_max = st.slider("Erlaubte Höhen (ft MSL)", 0, 10000, (0, 3000), step=100)
rate_limit = st.slider("Maximale Steig-/Sinkrate (m/s)", 0.0, 8.0, 2.0, step=0.5)

# --- Beispiel-Windprofil ---
wind_profile = [
    {"height": 0, "wind": [1.0, 0.0]},
    {"height": 500, "wind": [0.5, 0.5]},
    {"height": 1000, "wind": [0.0, 1.0]},
    {"height": 1500, "wind": [-0.5, 0.5]},
    {"height": 2000, "wind": [-1.0, 0.0]}
]

# --- ILP-Simulation ---
valid_layers = [w for w in wind_profile if height_min <= w["height"] <= height_max]

ilp_candidates = []
for w in valid_layers:
    h_ft = w["height"]
    h_m = h_ft * 0.3048
    t = (2 * h_m) / rate_limit  # Zeit in Sekunden

    dx = -w["wind"][0] * t  # negativer Drift (Rückwärts)
    dy = -w["wind"][1] * t

    candidate = {
        "easting": easting + dx,
        "northing": northing + dy
    }
    ilp_candidates.append(candidate)

if ilp_candidates:
    avg_e = np.mean([p["easting"] for p in ilp_candidates])
    avg_n = np.mean([p["northing"] for p in ilp_candidates])
    ilp_lat, ilp_lon = utm.to_latlon(avg_e, avg_n, zone_number, zone_letter)

    st.subheader("Berechneter ILP-Bereich")
    st.write(f"Mittlerer ILP: {avg_e:.1f} E / {avg_n:.1f} N (Zone {zone})")
    st.map(pd.DataFrame([{"lat": ilp_lat, "lon": ilp_lon}]))

    st.success("ILP-Bereich erfolgreich berechnet.")
else:
    st.warning("Keine gültige Höhe im Windprofil ausgewählt.")
