
# HAB CompetitionBrain Kindermann-Schön – Version 3.3

import streamlit as st
import pandas as pd
import math
import folium
from streamlit_folium import st_folium
import utm

# === Konstante Startwerte für Bad Waltersdorf ===
ZONE_NUMBER = 33
ZONE_LETTER = 'T'
DEFAULT_EAST = 576010
DEFAULT_NORTH = 5224670

def parse_utm_input(eingabe_ost, eingabe_nord, format):
    try:
        if format == "4/4":
            return int("57" + eingabe_ost), int("522" + eingabe_nord)
        elif format == "5/4":
            return int(eingabe_ost), int("522" + eingabe_nord)
        else:
            return None, None
    except:
        return None, None

def calculate_ilp_center(e, n, wind_df, height_min, height_max, max_rate, radius_km):
    wind_df = wind_df[(wind_df["Altitude (ft MSL)"] >= height_min) & (wind_df["Altitude (ft MSL)"] <= height_max)]
    if wind_df.empty:
        return None, "Keine Winddaten im Höhenbereich"

    candidates = []
    for _, row in wind_df.iterrows():
        heading_deg = row["Wind heading (true deg)"]
        speed_kmh = row["Wind speed (km/h)"]
        speed_ms = speed_kmh / 3.6

        h_m = row["Altitude (ft MSL)"] * 0.3048
        time_up_down = (2 * h_m) / max_rate

        dx = -math.sin(math.radians(heading_deg)) * speed_ms * time_up_down
        dy = -math.cos(math.radians(heading_deg)) * speed_ms * time_up_down

        candidates.append((e + dx, n + dy))

    if not candidates:
        return None, "Keine Kandidaten berechnet"

    avg_e = sum(p[0] for p in candidates) / len(candidates)
    avg_n = sum(p[1] for p in candidates) / len(candidates)
    return (avg_e, avg_n), None

def startseite():
    st.title("HAB CompetitionBrain Kindermann-Schön – v3.3")

    st.header("1) Windprofil")
    uploaded_file = st.file_uploader("Winddaten (.txt)", type="txt")

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, sep="\t", comment="#", engine="python")
            df.columns = ["Altitude (ft MSL)", "Wind heading (true deg)", "Wind speed (km/h)"]
            st.session_state.wind_df = df
            st.success("Winddaten geladen.")
        except Exception as e:
            st.error(f"Fehler beim Einlesen: {e}")

    if "wind_df" in st.session_state:
        st.header("2) Berechnen")
        if st.button("ILP"):
            st.session_state.page = "ILP"
            st.experimental_rerun()

    st.header("3) Weitere Funktionen")
    st.markdown("* Marker-Drop (folgt)")
    st.markdown("* Steigen/Sinken (folgt)")
    st.markdown("* Einheiten umrechnen (folgt)")

def ilp_seite():
    st.header("ILP – Individual Launch Point")
    st.markdown("### Zielkoordinate (UTM-Auszug)")

    format = st.selectbox("Koordinatenformat", ["4/4", "5/4"])
    eingabe_ost = st.text_input("Ostwert", "7601")
    eingabe_nord = st.text_input("Nordwert", "2467")
    ziel_e, ziel_n = parse_utm_input(eingabe_ost, eingabe_nord, format)

    st.markdown("### Einstellungen für ILP-Bereich")
    distanz = st.slider("Gewünschte Startdistanz vom Ziel (km)", 0, 15, (2, 4))
    hoehe = st.slider("Verwendete Höhen (ft MSL)", 0, 10000, (0, 3000), step=100)
    rate = st.slider("Maximale Steig-/Sinkrate (m/s)", 0.5, 8.0, 2.0, step=0.5)

    if ziel_e and ziel_n:
        st.markdown(f"Ziel (UTM): {ziel_e}, {ziel_n}")
        try:
            lat, lon = utm.to_latlon(ziel_e, ziel_n, ZONE_NUMBER, ZONE_LETTER)
            st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

            if "wind_df" in st.session_state:
                mp_coords, fehler = calculate_ilp_center(ziel_e, ziel_n, st.session_state.wind_df, hoehe[0], hoehe[1], rate, distanz[1])
                if mp_coords:
                    mp_lat, mp_lon = utm.to_latlon(mp_coords[0], mp_coords[1], ZONE_NUMBER, ZONE_LETTER)
                    st.success(f"Vorgeschlagener Startmittelpunkt: {mp_coords[0]:.1f} / {mp_coords[1]:.1f} (UTM)")

                    # Karte mit Kreis
                    m = folium.Map(location=[lat, lon], zoom_start=13, tiles="OpenStreetMap")
                    folium.Marker([lat, lon], tooltip="Ziel", icon=folium.Icon(color="red")).add_to(m)
                    folium.Marker([mp_lat, mp_lon], tooltip="Start-Mittelpunkt", icon=folium.Icon(color="green")).add_to(m)
                    folium.Circle(
                        location=[lat, lon],
                        radius=distanz[1] * 1000,
                        color="blue",
                        fill=True,
                        fill_opacity=0.3,
                        tooltip="Möglicher ILP-Bereich"
                    ).add_to(m)
                    st_folium(m, width=700, height=500)
                else:
                    st.error(fehler)
            else:
                st.warning("Kein Windprofil geladen.")
        except Exception as e:
            st.error(f"Koordinatenproblem: {e}")
    else:
        st.error("Ungültige Zielkoordinaten")

    if st.button("Zurück zur Startseite"):
        st.session_state.page = "Startseite"
        st.experimental_rerun()

def main():
    if "page" not in st.session_state:
        st.session_state.page = "Startseite"
    if st.session_state.page == "Startseite":
        startseite()
    elif st.session_state.page == "ILP":
        ilp_seite()

main()
