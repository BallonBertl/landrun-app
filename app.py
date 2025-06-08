# HAB CompetitionBrain Kindermann-Schön – Vollständiger Streamlit-Code
import streamlit as st
import utm
import numpy as np
import pandas as pd

# Globale Zustände
if "wind_data" not in st.session_state:
    st.session_state.wind_data = []
if "wind_ready" not in st.session_state:
    st.session_state.wind_ready = False

# ----------------------
# STARTSEITE
# ----------------------
def startseite():
    st.title("HAB CompetitionBrain Kindermann-Schön")

    st.header("1) Windprofil eingeben")
    with st.form("wind_input_form"):
        num_layers = st.number_input("Anzahl Windschichten", min_value=1, max_value=20, value=5)
        wind_data = []
        for i in range(num_layers):
            cols = st.columns(3)
            height = cols[0].number_input(f"Höhe {i+1} (ft)", key=f"h_{i}")
            dir_deg = cols[1].number_input(f"Richtung (°)", min_value=0, max_value=360, key=f"d_{i}")
            speed = cols[2].number_input(f"Geschwindigkeit (m/s)", min_value=0.0, key=f"s_{i}")
            # Richtungsvektor berechnen
            dir_rad = np.radians(dir_deg)
            wind_vector = [np.sin(dir_rad) * speed, np.cos(dir_rad) * speed]
            wind_data.append({ "height": height, "wind": wind_vector })

        submitted = st.form_submit_button("Windprofil speichern")
        if submitted:
            st.session_state.wind_data = wind_data
            st.session_state.wind_ready = True
            st.success("Windprofil erfolgreich gespeichert.")

    st.divider()
    st.header("2) Aufgabe auswählen")

    if st.session_state.wind_ready:
        col1, col2 = st.columns(3)[0:2]
        if col1.button("Aufgabe 1: ILP"):
            st.session_state.page = "ILP"
        # Weitere Aufgaben-Buttons hier ergänzen (PDG, CRT, etc.)
    else:
        st.info("Bitte zuerst ein gültiges Windprofil eingeben, um Aufgaben zu aktivieren.")

# ----------------------
# AUFGABE ILP
# ----------------------
def ilp_seite():
    st.title("ILP – Individual Launch Point")

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

    wind_profile = st.session_state.wind_data
    valid_layers = [w for w in wind_profile if height_min <= w["height"] <= height_max]

    ilp_candidates = []
    for w in valid_layers:
        h_m = w["height"] * 0.3048
        t = (2 * h_m) / rate_limit
        dx = -w["wind"][0] * t
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

    if st.button("Zurück zur Startseite"):
        st.session_state.page = "START"

# ----------------------
# SEITENSTEUERUNG
# ----------------------
if "page" not in st.session_state:
    st.session_state.page = "START"

if st.session_state.page == "START":
    startseite()
elif st.session_state.page == "ILP":
    ilp_seite()
