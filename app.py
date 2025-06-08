# HAB CompetitionBrain Kindermann-Schön – v1.7
# Erstellt am 2025-06-08 20:09:31

# -- Import-Module --
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import utm
import math

# -- Seitenkonfiguration --
st.set_page_config(page_title="HAB CompetitionBrain Kindermann-Schön – v1.7")

# -- Session State Initialisierung --
if "wind_df" not in st.session_state:
    st.session_state.wind_df = pd.DataFrame()
if "wind_loaded" not in st.session_state:
    st.session_state.wind_loaded = False

# -- Funktionen --

def parse_uploaded_file(upload):
    try:
        df = pd.read_csv(upload, sep="\t", skiprows=2, engine="python", header=None)
        df.columns = ["Höhe (ft)", "Richtung (°)", "Geschwindigkeit (km/h)"]
        st.session_state.wind_df = df
        st.session_state.wind_loaded = True
    except Exception as e:
        st.error(f"Fehler beim Laden: {e}")

def convert_to_utm(eingabe_ost, eingabe_nord, format, zone="33T"):
    base_e, base_n = 576000, 5224000  # Bad Waltersdorf
    if format == "4/4":
        return base_e - (base_e % 10000) + eingabe_ost, base_n - (base_n % 10000) + eingabe_nord
    elif format == "5/4":
        return base_e - (base_e % 100000) + eingabe_ost, base_n - (base_n % 10000) + eingabe_nord
    return None, None

def ilp_seite():
    st.markdown("## ILP – Individual Launch Point")
    st.markdown("### Zielkoordinate")

    format = st.radio("Koordinatenformat", ["4/4", "5/4"], index=0)
    ost = st.number_input("UTM-Ostwert", value=7601 if format == "4/4" else 57601)
    nord = st.number_input("UTM-Nordwert", value=2467)

    ziel_e, ziel_n = convert_to_utm(int(ost), int(nord), format)
    if not ziel_e or not ziel_n:
        st.stop()

    st.markdown("### Einstellungen für ILP-Bereich")

    distanz = st.slider("Gewünschte Startdistanz vom Ziel (km)", 0, 15, (2, 4))
    hoehen_ft = st.slider("Erlaubte Höhen (ft MSL)", 0, 10000, (0, 3000), step=100)
    rate = st.slider("Max. Steig-/Sinkrate (m/s)", 0.0, 8.0, 2.0, step=0.5)

    if not st.session_state.wind_loaded:
        st.warning("Bitte zuerst Winddaten auf der Startseite eingeben.")
        return

    df = st.session_state.wind_df.copy()
    df = df[(df["Höhe (ft)"] >= hoehen_ft[0]) & (df["Höhe (ft)"] <= hoehen_ft[1])]
    if df.empty:
        st.error("Kein Windprofil in diesem Höhenbereich.")
        return

    kreispunkte = []
    for _, row in df.iterrows():
        windrichtung = row["Richtung (°)"]
        windgeschw_kmh = row["Geschwindigkeit (km/h)"]
        windgeschw_ms = windgeschw_kmh / 3.6
        steigezeit = (2 * (row["Höhe (ft)"] * 0.3048)) / rate  # m to m, v in m/s
        distanz_m = windgeschw_ms * steigezeit
        rückrichtung_rad = math.radians((windrichtung + 180) % 360)
        dx = math.sin(rückrichtung_rad) * distanz_m
        dy = math.cos(rückrichtung_rad) * distanz_m
        kreispunkte.append((ziel_e + dx, ziel_n + dy))

    mp_e = sum(p[0] for p in kreispunkte) / len(kreispunkte)
    mp_n = sum(p[1] for p in kreispunkte) / len(kreispunkte)

    try:
        mp_lat, mp_lon = utm.to_latlon(mp_e, mp_n, 33, "T")
        ziel_lat, ziel_lon = utm.to_latlon(ziel_e, ziel_n, 33, "T")
        m = folium.Map(location=[ziel_lat, ziel_lon], zoom_start=13, tiles="OpenStreetMap")
        folium.Marker(location=[ziel_lat, ziel_lon], popup="Ziel").add_to(m)
        folium.Circle(location=[mp_lat, mp_lon], radius=distanz[1]*1000,
                      color="green", fill=True, fill_opacity=0.4).add_to(m)
        folium.Marker(location=[mp_lat, mp_lon], popup="Vorgeschlagener ILP", icon=folium.Icon(color="green")).add_to(m)
        st_data = st_folium(m, width=700, height=500)

        st.success(f"Vorgeschlagene Startkoordinate: {str(int(mp_e))[-5:] if format=='5/4' else str(int(mp_e))[-4:]} / {str(int(mp_n))[-4:]}")
    except Exception as e:
        st.error(f"Fehler bei Kartenanzeige: {e}")

    if st.button("Zurück zur Startseite"):
        st.experimental_rerun()

def startseite():
    st.title("HAB CompetitionBrain Kindermann-Schön")
    st.header("1) Windprofil")
    tab1, tab2 = st.tabs(["Winddatei hochladen", "Manuell eingeben"])

    with tab1:
        upload = st.file_uploader("Winddaten als .txt", type=["txt"])
        if upload:
            parse_uploaded_file(upload)
    with tab2:
        df = st.data_editor(pd.DataFrame({
            "Höhe (ft)": [],
            "Richtung (°)": [],
            "Geschwindigkeit (km/h)": []
        }), num_rows="dynamic")
        if not df.empty:
            st.session_state.wind_df = df
            st.session_state.wind_loaded = True

    st.header("2) Berechnungen")
    if st.session_state.wind_loaded:
        if st.button("ILP"):
            st.session_state["seite"] = "ilp"
    else:
        st.info("Bitte zuerst Winddaten eingeben.")

    st.header("Weitere Funktionen")
    st.button("MarkerDrop (Platzhalter)")
    st.button("Steigen/Sinken (Platzhalter)")
    st.button("Einheiten umrechnen (Platzhalter)")

# -- Hauptlogik --
if "seite" not in st.session_state:
    st.session_state["seite"] = "start"

if st.session_state["seite"] == "start":
    startseite()
elif st.session_state["seite"] == "ilp":
    ilp_seite()
