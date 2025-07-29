
# HAB CompetitionBrain Kindermann-Schön – Version Dreiecksfläche v1.7 (vereinfacht)
import streamlit as st
import pandas as pd
import numpy as np
import io
from math import sqrt
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Dreiecksfläche – v1.7", layout="wide")

# Zielkoordinate: Fixpunkt Bad Waltersdorf (UTM: 576010 / 5224670 – Zone 33T)
ziel_e = 576010
ziel_n = 5224670
zone_number = 33
zone_letter = 'T'

if "wind_df" not in st.session_state:
    st.session_state.wind_df = pd.DataFrame(columns=["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"])

st.title("🔺 Größtmögliche Dreiecksfläche – Version v1.7 (vereinfacht)")
st.caption("Zielpunkt fix: Bad Waltersdorf")

uploaded_file = st.file_uploader("Winddatei hochladen (.txt oder .csv)", type=["txt", "csv"])
if uploaded_file is not None:
    try:
        lines = uploaded_file.read().decode("utf-8").splitlines()
        data_lines = [line for line in lines if not line.startswith("#") and line.strip() != ""]
        df = pd.read_csv(io.StringIO("\n".join(data_lines)), sep="\t", header=None)
        if df.shape[1] >= 3:
            df.columns = ["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"]
            st.session_state.wind_df = df
            st.success("Windprofil erfolgreich geladen.")
        else:
            st.error("Nicht genügend Spalten gefunden.")
    except Exception as e:
        st.error(f"Fehler beim Verarbeiten der Datei: {e}")

if not st.session_state.wind_df.empty:
    st.header("Einstellungen für Berechnung")
    height_min, height_max = st.slider("Erlaubte Höhen (ft MSL)", 0, 10000, (0, 3000), step=100)
    rate_limit = st.slider("Maximale Steig-/Sinkrate (m/s)", 0.0, 8.0, 2.0, step=0.5)

    df = st.session_state.wind_df
    wind_profile = []
    for _, row in df.iterrows():
        try:
            h = float(row["Höhe [ft]"])
            deg = float(row["Richtung [°]"])
            spd_kmh = float(row["Geschwindigkeit [km/h]"])
        except:
            continue
        spd_ms = spd_kmh / 3.6
        dir_rad = np.radians(deg)
        wind_vector = [np.sin(dir_rad) * spd_ms, np.cos(dir_rad) * spd_ms]
        wind_profile.append({ "height": h, "wind": wind_vector })

    valid_layers = [w for w in wind_profile if height_min <= w["height"] <= height_max]

    punkte = []
    for w in valid_layers:
        h_m = w["height"] * 0.3048
        t = (2 * h_m) / rate_limit
        dx = -w["wind"][0] * t
        dy = -w["wind"][1] * t
        x = ziel_e + dx
        y = ziel_n + dy
        punkte.append((x, y))

    if len(punkte) >= 3:
        punkte_np = np.array(punkte)
        from scipy.spatial import ConvexHull
        hull = ConvexHull(punkte_np)
        flaeche_m2 = hull.area
        flaeche_km2 = flaeche_m2 / 1e6

        st.success(f"Größtmögliche umschlossene Fläche: {flaeche_km2:.2f} km²")

        import utm
        m = folium.Map(location=[47.0667, 15.9333], zoom_start=12)
        for p in punkte_np[hull.vertices]:
            lat, lon = utm.to_latlon(p[0], p[1], zone_number, zone_letter)
            folium.CircleMarker([lat, lon], radius=4, color="blue").add_to(m)
        folium.Marker([47.0667, 15.9333], popup="Ziel (Bad Waltersdorf)", icon=folium.Icon(color="red")).add_to(m)
        st_folium(m, width=700, height=500)
    else:
        st.warning("Nicht genügend Punkte für eine Flächenberechnung.")
