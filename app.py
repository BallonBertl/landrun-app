
# HAB CompetitionBrain Kindermann-Schön – Version ILP 1.7
import streamlit as st
import pandas as pd
import numpy as np
import utm
import io
from math import sqrt
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="HAB CompetitionBrain Kindermann-Schön")

if "wind_df" not in st.session_state:
    st.session_state.wind_df = pd.DataFrame(columns=["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"])
if "wind_ready" not in st.session_state:
    st.session_state.wind_ready = False
if "page" not in st.session_state:
    st.session_state.page = "START"
    st.session_state.trigger_ilp = False
    st.session_state.page = "START"

def startseite():
    st.title("HAB CompetitionBrain Kindermann-Schön")
    st.caption("🛠 DEBUG: Version ILP 1.7 – 9. Juni 2025")

    st.header("1) Windprofil eingeben")
    upload_col, manual_col = st.columns(2)

    with upload_col:
        uploaded_file = st.file_uploader("Winddatei hochladen (.txt oder .csv)", type=["txt", "csv"])
        if uploaded_file is not None:
            try:
                lines = uploaded_file.read().decode("utf-8").splitlines()
                data_lines = [line for line in lines if not line.startswith("#") and line.strip() != ""]
                df = pd.read_csv(io.StringIO("\n".join(data_lines)), sep="\t", header=None)
                if df.shape[1] >= 3:
                    df.columns = ["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"]
                    st.session_state.wind_df = df
                    st.session_state.wind_ready = True
                    st.success("Windprofil erfolgreich geladen.")

else:
                    st.error("Datei erkannt, aber nicht genügend Spalten gefunden.")
            except Exception as e:
                st.error(f"Fehler beim Verarbeiten der Datei: {e}")

    
    with manual_col:
        st.write("Oder manuelle Eingabe:")
        st.session_state.wind_df = st.data_editor(
            st.session_state.wind_df,
            num_rows="dynamic",
            use_container_width=True
        )
        if not st.session_state.wind_df.empty:
            st.session_state.wind_ready = True


    st.divider()
    st.header("2) Tools und Aufgaben")
    st.subheader("Tools (immer verfügbar):")
    st.button("📍 Markerdrop (folgt)", disabled=True)
    st.button("⏬ Steigen/Sinken (folgt)", disabled=True)
    st.button("🔄 Einheiten umrechnen (folgt)", disabled=True)

    if st.session_state.wind_ready:
        st.subheader("Aufgaben (aktiv nach Winddaten):")
        if st.button("ILP"):
            st.session_state.page = "ILP"

else:
        st.info("Bitte zuerst gültige Winddaten eingeben, um Aufgaben freizuschalten.")

def ilp_seite():
    st.title("ILP – Individual Launch Point")

    st.subheader("🎯 Zielkoordinate (UTM)")
    zone = st.selectbox("UTM-Zone", ["32T", "33T", "34T"], index=1)
    zone_number = int(zone[:-1])
    zone_letter = zone[-1]

    format = st.selectbox("Koordinatenformat", ["4/4", "5/4"])
    if format == "4/4":
        east_part = st.text_input("Ostwert (4 Stellen)", value="7601")
        north_part = st.text_input("Nordwert (4 Stellen)", value="2467")
        try:
            easting = 500000 + int(east_part) * 10
            northing = 5200000 + int(north_part) * 10
        except:
            st.error("Ungültige Eingabe.")
            return

else:
        east_part = st.text_input("Ostwert (5 Stellen)", value="57601")
        north_part = st.text_input("Nordwert (4 Stellen)", value="2467")
        try:
            easting = int(east_part) * 10
            northing = 5200000 + int(north_part) * 10
        except:
            st.error("Ungültige Eingabe.")
            return

    lat, lon = utm.to_latlon(easting, northing, zone_number, zone_letter)
    st.caption(f"WGS84 Zielkoordinate: {lat:.6f}, {lon:.6f}")

    st.subheader("🧭 Einstellungen für ILP-Bereich")
    range_km = st.slider("Gewünschte Startdistanz (km)", 0, 15, (2, 4))
    height_min, height_max = st.slider("Erlaubte Höhen (ft MSL)", 0, 10000, (0, 3000), step=100)
    rate_limit = st.slider("Maximale Steig-/Sinkrate (m/s)", 0.0, 8.0, 2.0, step=0.5)
    map_style = st.selectbox("Kartenstil", ["OpenStreetMap", "Esri.WorldImagery", "Stamen Terrain", "CartoDB positron"])

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

    ilp_candidates = []
    for w in valid_layers:
        h_m = w["height"] * 0.3048
        t = (2 * h_m) / rate_limit
        dx = -w["wind"][0] * t
        dy = -w["wind"][1] * t
        x = easting + dx
        y = northing + dy
        dist = sqrt((x - easting)**2 + (y - northing)**2)
        if range_km[0]*1000 <= dist <= range_km[1]*1000:
            ilp_candidates.append({ "easting": x, "northing": y })

    if ilp_candidates:
        avg_e = np.mean([p["easting"] for p in ilp_candidates])
        avg_n = np.mean([p["northing"] for p in ilp_candidates])
        max_dist = max([sqrt((p["easting"] - avg_e)**2 + (p["northing"] - avg_n)**2) for p in ilp_candidates])
        radius_km = max_dist / 1000
        ilp_lat, ilp_lon = utm.to_latlon(avg_e, avg_n, zone_number, zone_letter)

        st.subheader("📌 Ergebnis")

        if format == "4/4":
            ilp_e_out = int((avg_e - 500000) / 10)
            ilp_n_out = int((avg_n - 5200000) / 10)

else:
            ilp_e_out = int(avg_e / 10)
            ilp_n_out = int((avg_n - 5200000) / 10)

        st.success(f"ILP-Mittelpunkt (Vorschlag): {ilp_e_out} / {ilp_n_out} ({format}) – Radius: {radius_km:.2f} km")
        st.caption(f"WGS84: {ilp_lat:.6f}, {ilp_lon:.6f}")

        m = folium.Map(
        location=[lat, lon],
        zoom_start=13,
        tiles="https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
        attr="Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL."
    )
        folium.Marker([lat, lon], popup="Ziel", icon=folium.Icon(color="red")).add_to(m)
        folium.Marker([ilp_lat, ilp_lon], popup="ILP-Mittelpunkt", icon=folium.Icon(color="green")).add_to(m)
        folium.Circle(
            location=[ilp_lat, ilp_lon],
            radius=radius_km * 1000,
            color="green",
            fill=True,
            fill_opacity=0.4
        ).add_to(m)
        st_data = st_folium(m, width=700, height=500)

else:
        st.warning("Keine gültigen Startpunkte innerhalb der gewünschten Distanz gefunden.")

    if st.button("🔙 Zurück zur Startseite"):
        st.session_state.page = "START"
        
if st.session_state.page == "START":
    startseite()
elif st.session_state.page == "ILP":
    ilp_seite()


 [deaktiviert – nur am Dateiende erlaubt]


# ✅ Sichere Navigation (außerhalb aller Funktionen)
if st.session_state.trigger_ilp:
    st.session_state.page = "ILP"
    st.session_state.trigger_ilp = False
    st.experimental_rerun()
