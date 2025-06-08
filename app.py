
import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import math
import utm

# App-Konfiguration
st.set_page_config(page_title="HAB CompetitionBrain Kindermann-Schön – v3.0")

# Zielkoordinaten Bad Waltersdorf
ZIEL_UTM_E = 576010
ZIEL_UTM_N = 5224670
UTM_ZONE = "33T"

# Funktion zur Umrechnung von 4/4 oder 5/4-Koordinaten in vollständige UTM
def expand_coords(x_short, y_short, format_option):
    if format_option == "4/4":
        return int("57" + str(x_short)), int("522" + str(y_short))
    elif format_option == "5/4":
        return int("576" + str(x_short)), int("522" + str(y_short))
    return x_short, y_short

# Winddaten-Vorbereitung
def parse_wind_data(uploaded_file):
    wind_df = pd.read_csv(uploaded_file, sep="\t", comment="#", engine="python")
    wind_df.columns = ["Altitude_ft", "Wind_Dir", "Wind_Speed_kmh"]
    return wind_df

# Rückwärtssimulation des ILP-Bereichs
def berechne_ilp_bereich(wind_df, ziel_e, ziel_n, hoehen_ft, rate_ms, distanz_km):
    ilp_kandidaten = []

    for _, row in wind_df.iterrows():
        hoehe = row["Altitude_ft"]
        if hoehen_ft[0] <= hoehe <= hoehen_ft[1]:
            richtung_deg = row["Wind_Dir"]
            geschw_kmh = row["Wind_Speed_kmh"]
            geschw_ms = geschw_kmh / 3.6

            t_gesamt = (2 * hoehe * 0.3048) / rate_ms  # s
            dx = -geschw_ms * t_gesamt * math.sin(math.radians(richtung_deg))
            dy = -geschw_ms * t_gesamt * math.cos(math.radians(richtung_deg))

            ilp_kandidaten.append((ziel_e + dx, ziel_n + dy))

    if len(ilp_kandidaten) == 0:
        return ziel_e, ziel_n, 0

    punkte = np.array(ilp_kandidaten)
    mittelpunkt = np.mean(punkte, axis=0)
    radius = distanz_km * 1000

    return mittelpunkt[0], mittelpunkt[1], radius

# Seitenlogik
def startseite():
    st.title("HAB CompetitionBrain Kindermann-Schön – v3.0")

    if "wind_df" not in st.session_state:
        st.session_state.wind_df = None

    st.header("1) Winddaten eingeben")
    upload_col, manual_col = st.columns(2)

    with upload_col:
        uploaded_file = st.file_uploader("Winddatei (.txt)", type=["txt"])
        if uploaded_file is not None:
            try:
                st.session_state.wind_df = parse_wind_data(uploaded_file)
                st.success("Winddaten erfolgreich geladen.")
            except Exception as e:
                st.error(f"Fehler beim Laden: {e}")

    with manual_col:
        st.info("Manuelle Eingabe in Vorbereitung")

    st.header("2) Berechnen")
    if st.session_state.wind_df is not None:
        if st.button("ILP"):
            st.session_state.page = "ilp"

    st.header("Weitere Tools")
    st.button("Markerdrop (in Arbeit)")
    st.button("Steigen/Sinken (in Arbeit)")
    st.button("Einheiten umrechnen (in Arbeit)")

def ilp_seite():
    st.title("ILP – Individual Launch Point")
    st.button("Zurück zur Startseite", on_click=lambda: st.session_state.update(page="start"))

    st.subheader("Zielkoordinate (UTM)")
    format_option = st.selectbox("Koordinatenformat", ["4/4", "5/4"])
    x_short = st.number_input("UTM Ostwert (kurz)", value=6010 if format_option=="4/4" else 76010)
    y_short = st.number_input("UTM Nordwert (kurz)", value=24670)

    ziel_e, ziel_n = expand_coords(x_short, y_short, format_option)

    latlon = utm.to_latlon(ziel_e, ziel_n, 33, 'T')
    st.write(f"WGS84: {latlon[0]:.5f} N, {latlon[1]:.5f} E")

    st.subheader("Einstellungen für ILP-Bereich")
    distanz = st.slider("Gewünschte Startdistanz (km)", 0, 15, (2, 4))
    hoehen_ft = st.slider("Verwendete Höhen (ft MSL)", 0, 10000, (0, 3000), step=100)
    rate_ms = st.slider("Maximale Steig-/Sinkrate (m/s)", 0.5, 8.0, 2.0, step=0.5)

    if st.button("ILP-Bereich berechnen"):
        wind_df = st.session_state.wind_df
        mp_e, mp_n, radius = berechne_ilp_bereich(wind_df, ziel_e, ziel_n, hoehen_ft, rate_ms, distanz[1])
        mp_lat, mp_lon = utm.to_latlon(mp_e, mp_n, 33, 'T')
        ziel_lat, ziel_lon = utm.to_latlon(ziel_e, ziel_n, 33, 'T')

        st.map(pd.DataFrame([[mp_lat, mp_lon]], columns=["lat", "lon"]))

        m = folium.Map(location=[ziel_lat, ziel_lon], zoom_start=13, tiles="OpenStreetMap")
        folium.Marker([ziel_lat, ziel_lon], tooltip="Ziel", icon=folium.Icon(color="red")).add_to(m)
        folium.Circle([mp_lat, mp_lon], radius=radius, tooltip="Möglicher ILP", color="green", fill_opacity=0.3).add_to(m)
        st_folium(m, height=500)

        mp_short_x = str(int(mp_e))[-4:] if format_option == "4/4" else str(int(mp_e))[-5:]
        mp_short_y = str(int(mp_n))[-4:]
        st.write(f"Vorgeschlagener ILP (Koordinate {format_option}): {mp_short_x} / {mp_short_y}")

# Routing
if "page" not in st.session_state:
    st.session_state.page = "start"

if st.session_state.page == "start":
    startseite()
elif st.session_state.page == "ilp":
    ilp_seite()
