# HAB CompetitionBrain Kindermann-Schön – Version 3.4
# Komplettversion mit stabiler Startseite, funktionierendem Windeditor, ILP mit Ziel/Start-UTM (4/4 oder 5/4), Kartenanzeige, Rundum-Korrekturen

import streamlit as st
import pandas as pd
import numpy as np
import math
import utm
import folium
from streamlit_folium import st_folium

# ------------------------------ Initialisierung ------------------------------ #
st.set_page_config(page_title="HAB CompetitionBrain Kindermann-Schön – v3.4", layout="centered")

if "wind_df" not in st.session_state:
    st.session_state.wind_df = pd.DataFrame(columns=["Altitude (ft MSL)", "Wind direction (°)", "Wind speed (km/h)"])

if "seite" not in st.session_state:
    st.session_state.seite = "start"

# ------------------------------ Navigation ------------------------------ #
def zeige_navi_buttons():
    st.divider()
    cols = st.columns(4)
    if st.session_state.wind_df.empty:
        with cols[0]:
            st.button("ILP", on_click=lambda: st.warning("Bitte zuerst Winddaten eingeben."))
    else:
        with cols[0]:
            if st.button("ILP"):
                st.session_state.seite = "ilp"
                st.experimental_rerun()
    with cols[1]:
        st.button("Markerdrop", disabled=True)
    with cols[2]:
        st.button("Steigen/Sinken", disabled=True)
    with cols[3]:
        st.button("Einheiten umrechnen", disabled=True)

# ------------------------------ Startseite ------------------------------ #
def startseite():
    st.title("HAB CompetitionBrain Kindermann-Schön")

    tab1, tab2 = st.tabs(["Winddaten aus Datei", "Winddaten manuell eingeben"])

    with tab1:
        uploaded_file = st.file_uploader("Lade eine Winddatei im .txt-Format hoch", type="txt")
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file, comment="#", delimiter=r"\s+", engine="python")
                df.columns = ["Altitude (ft MSL)", "Wind direction (°)", "Wind speed (km/h)"]
                st.session_state.wind_df = df
                st.success("Winddaten erfolgreich geladen.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Fehler beim Laden: {e}")

    with tab2:
        st.session_state.wind_df = st.data_editor(
            st.session_state.wind_df,
            num_rows="dynamic",
            use_container_width=True,
            key="wind_editor"
        )

    zeige_navi_buttons()

# ------------------------------ ILP-Unterseite ------------------------------ #
def ilp_seite():
    st.header("ILP – Individual Launch Point")
    st.subheader("Zielkoordinate (UTM-Auszug)")

    format = st.selectbox("Koordinatenformat", ["4/4", "5/4"], index=0)
    zone = "33T"
    default_utm = (576010, 5224670)  # Bad Waltersdorf
    short_east = int(str(default_utm[0])[-5:]) if format == "5/4" else int(str(default_utm[0])[-4:])
    short_north = int(str(default_utm[1])[-4:])

    col1, col2 = st.columns(2)
    with col1:
        e_in = st.text_input("UTM-Ostwert", value=str(short_east))
    with col2:
        n_in = st.text_input("UTM-Nordwert", value=str(short_north))

    # Umrechnung aus 4/4 oder 5/4 auf vollständige Koordinate
    try:
        e_len = 5 if format == "5/4" else 4
        e_off = int(str(default_utm[0])[:6 - e_len])
        full_e = int(str(e_off) + e_in)
        full_n = int(str(default_utm[1])[:3] + n_in)
        ziel_e, ziel_n = full_e, full_n
    except:
        st.error("Ungültige UTM-Eingabe.")
        return

    # Anzeige der Einstellungen für ILP-Bereich
    st.subheader("Einstellungen für ILP-Bereich")
    radius_km = st.slider("Gewünschte Startdistanz (km)", 0.5, 15.0, (2.0, 4.0), step=0.5)
    height_min, height_max = st.slider("Erlaubte Höhen (ft MSL)", 0, 10000, (0, 3000), step=100)
    max_rate = st.slider("Maximale Steig-/Sinkrate (m/s)", 0.5, 8.0, 2.0, step=0.5)

    # Winddaten vorbereiten
    df = st.session_state.wind_df.copy()
    df = df[(df["Altitude (ft MSL)"] >= height_min) & (df["Altitude (ft MSL)"] <= height_max)]
    if df.empty:
        st.error("Keine Winddaten in diesem Höhenbereich.")
        return

    vectors = []
    for _, row in df.iterrows():
        heading_rad = math.radians(row["Wind direction (°)"])
        spd_kmh = row["Wind speed (km/h)"]
        spd_ms = spd_kmh / 3.6  # nur intern für Vektorrechnung
        up_down_time = (2 * (row["Altitude (ft MSL)"] * 0.3048)) / max_rate
        dx = -spd_ms * math.sin(heading_rad) * up_down_time
        dy = -spd_ms * math.cos(heading_rad) * up_down_time
        vectors.append((dx, dy))

    dx_avg = np.mean([v[0] for v in vectors])
    dy_avg = np.mean([v[1] for v in vectors])

    mp_e = ziel_e + dx_avg
    mp_n = ziel_n + dy_avg
    mp_lat, mp_lon = utm.to_latlon(mp_e, mp_n, 33, 'T')

    st.markdown(f"**Vorgeschlagener ILP-Mittelpunkt (UTM):** {str(mp_e)[:6]} / {str(mp_n)[-4:]}")

    # Karte anzeigen
    m = folium.Map(location=[mp_lat, mp_lon], zoom_start=13)
    folium.Circle(location=[mp_lat, mp_lon], radius=radius_km[1]*1000,
                  color="green", fill=True, fill_opacity=0.3).add_to(m)
    ziel_lat, ziel_lon = utm.to_latlon(ziel_e, ziel_n, 33, 'T')
    folium.Marker(location=[ziel_lat, ziel_lon], tooltip="Zielkoordinate", icon=folium.Icon(color="red")).add_to(m)
    folium.Marker(location=[mp_lat, mp_lon], tooltip="Vorgeschlagener ILP", icon=folium.Icon(color="green")).add_to(m)

    st_folium(m, width=700, height=500)

    st.button("Zurück zur Startseite", on_click=lambda: st.session_state.update({"seite": "start"}))

# ------------------------------ Hauptlogik ------------------------------ #
if st.session_state.seite == "start":
    startseite()
elif st.session_state.seite == "ilp":
    ilp_seite()
