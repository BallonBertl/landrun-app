import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium import Circle
from streamlit_folium import st_folium
import math
import utm

st.set_page_config(page_title="HAB CompetitionBrain Kindermann-Schön – v3.5")

# --- Startseite ---
def startseite():
    st.title("HAB CompetitionBrain Kindermann-Schön")
    st.header("Winddaten eingeben")

    option = st.radio("Eingabemethode wählen:", ("Winddaten aus Datei hochladen", "Winddaten manuell eingeben"))

    if option == "Winddaten aus Datei hochladen":
        uploaded_file = st.file_uploader("Winddatei (.txt) hochladen", type="txt")
        if uploaded_file is not None:
            try:
                lines = uploaded_file.read().decode("utf-8").splitlines()
                data = []
                for line in lines:
                    if line.startswith("#") or "Altitude" in line or line.strip() == "":
                        continue
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        try:
                            alt = float(parts[0])
                            hdg = float(parts[1])
                            spd = float(parts[2])
                            data.append((alt, hdg, spd))
                        except:
                            continue
                df = pd.DataFrame(data, columns=["Altitude_ft", "Windrichtung_deg", "Windgeschw_kmh"])
                st.session_state.wind_df = df
                st.success("Winddaten erfolgreich geladen.")
                st.dataframe(df)
            except Exception as e:
                st.error(f"Fehler beim Laden: {e}")
    else:
        if "wind_df" not in st.session_state:
            st.session_state.wind_df = pd.DataFrame({
                "Altitude_ft": [0, 1000, 2000],
                "Windrichtung_deg": [0, 90, 180],
                "Windgeschw_kmh": [10, 20, 30]
            })

        st.session_state.wind_df = st.data_editor(
            st.session_state.wind_df,
            num_rows="dynamic",
            use_container_width=True
        )

    st.header("Berechnen")
    if "wind_df" in st.session_state and not st.session_state.wind_df.empty:
        st.page_link("/ILP", label="ILP", icon="🎯")
    else:
        st.info("Bitte zuerst gültige Winddaten eingeben.")

    st.divider()
    st.page_link("/dummy1", label="Markerdrop", disabled=True)
    st.page_link("/dummy2", label="Steigen/Sinken", disabled=True)
    st.page_link("/dummy3", label="Einheiten umrechnen", disabled=True)

# --- ILP Unterseite ---
def ilp_seite():
    st.title("ILP – Individual Launch Point")

    st.subheader("Zielkoordinate (UTM)")
    format = st.selectbox("Koordinatenformat", ["4/4", "5/4"])
    if format == "4/4":
        ost = st.text_input("UTM-Ostwert", value="7601")
        nord = st.text_input("UTM-Nordwert", value="2467")
        try:
            ost_full = int("576000"[:6 - len(ost)] + ost)
            nord_full = int("5224000"[:7 - len(nord)] + nord)
        except:
            st.error("Ungültige Koordinate")
            return
    else:
        ost = st.text_input("UTM-Ostwert", value="57601")
        nord = st.text_input("UTM-Nordwert", value="2467")
        try:
            ost_full = int("576000"[:6 - len(ost)] + ost)
            nord_full = int("5224000"[:7 - len(nord)] + nord)
        except:
            st.error("Ungültige Koordinate")
            return

    ziel_e, ziel_n = ost_full, nord_full

    st.subheader("Einstellungen für ILP-Bereich")
    distanz = st.slider("Gewünschte Startdistanz vom Ziel (km)", 0, 15, (2, 4))
    hoehe = st.slider("Erlaubte Höhen (ft MSL)", 0, 10000, (0, 3000), step=100)
    rate = st.slider("Max. Steig-/Sinkrate (m/s)", 0.0, 8.0, 2.0, step=0.5)

    if st.button("ILP-Bereich berechnen"):
        df = st.session_state.get("wind_df")
        if df is None or df.empty:
            st.error("Keine Winddaten vorhanden.")
            return

        winds = df[(df["Altitude_ft"] >= hoehe[0]) & (df["Altitude_ft"] <= hoehe[1])]

        if winds.empty:
            st.error("Keine passenden Windschichten gefunden.")
            return

        punkte = []
        for _, row in winds.iterrows():
            h_m = row["Altitude_ft"] * 0.3048
            t = (2 * h_m) / rate
            richtung_rad = math.radians(row["Windrichtung_deg"])
            spd_kmh = row["Windgeschw_kmh"]
            spd_ms = spd_kmh / 3.6
            dx = -math.sin(richtung_rad) * spd_ms * t
            dy = -math.cos(richtung_rad) * spd_ms * t
            punkte.append((ziel_e + dx, ziel_n + dy))

        mp_e = np.mean([p[0] for p in punkte])
        mp_n = np.mean([p[1] for p in punkte])
        mp_lat, mp_lon = utm.to_latlon(mp_e, mp_n, 33, 'T')
        radius = distanz[1] * 1000

        st.success(f"Vorgeschlagener Mittelpunkt des ILP: {mp_e:.0f} / {mp_n:.0f} (UTM)")

        m = folium.Map(location=[mp_lat, mp_lon], zoom_start=13, tiles="OpenStreetMap")
        Circle(location=[mp_lat, mp_lon], radius=radius, color="green", fill=True, fill_opacity=0.3).add_to(m)
        folium.Marker([mp_lat, mp_lon], popup="Vorgeschlagener ILP", icon=folium.Icon(color="green")).add_to(m)
        ziel_lat, ziel_lon = utm.to_latlon(ziel_e, ziel_n, 33, 'T')
        folium.Marker([ziel_lat, ziel_lon], popup="Ziel", icon=folium.Icon(color="red")).add_to(m)

        st_folium(m, width=700, height=500)

    if st.button("Zurück zur Startseite"):
        st.switch_page("/")

# --- Navigation ---
if __name__ == "__main__":
    if "page" not in st.session_state:
        st.session_state.page = "start"

    page = st.session_state.page

    if page == "start":
        startseite()
    elif page == "ILP":
        ilp_seite()
    else:
        startseite()
