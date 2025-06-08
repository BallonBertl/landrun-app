
# HAB CompetitionBrain Kindermann-Schön – Version 3.2

import streamlit as st
import pandas as pd
import math
import folium
from streamlit_folium import st_folium
import utm

# Standardkoordinaten Bad Waltersdorf
DEFAULT_ZONE_NUMBER = 33
DEFAULT_ZONE_LETTER = 'T'
DEFAULT_EASTING = 576010
DEFAULT_NORTHING = 5224670

# Seitensteuerung
def main():
    st.set_page_config(page_title="HAB CompetitionBrain Kindermann-Schön – v3.2")
    if "page" not in st.session_state:
        st.session_state.page = "Startseite"
    if st.session_state.page == "Startseite":
        startseite()
    elif st.session_state.page == "ILP":
        ilp_seite()

def startseite():
    st.title("HAB CompetitionBrain Kindermann-Schön")
    st.markdown("### 1) Winddaten eingeben")
    wind_input = st.file_uploader("Lade eine .txt-Datei mit Winddaten hoch", type=["txt"])
    if wind_input:
        try:
            df = pd.read_csv(wind_input, sep="\t", comment="#", engine="python")
            df.columns = df.columns.str.strip()
            df = df.rename(columns=lambda x: x.strip())
            if "Altitude (f" in df.columns[0]:
                df.columns = ["Altitude_ft", "Wind_Direction", "Wind_Speed_kmh"]
            st.session_state.wind_df = df
            st.success("Winddaten erfolgreich geladen.")
        except Exception as e:
            st.error(f"Fehler beim Einlesen der Datei: {e}")

    if "wind_df" in st.session_state:
        st.markdown("### 2) Berechnung")
        if st.button("ILP"):
            st.session_state.page = "ILP"
            st.experimental_rerun()

    st.markdown("### Immer verfügbar:")
    st.button("Markerdrop (folgt)", disabled=True)
    st.button("Steigen/Sinken (folgt)", disabled=True)
    st.button("Einheiten umrechnen (folgt)", disabled=True)

def ilp_seite():
    st.title("ILP – Individual Launch Point")
    st.markdown("#### Zielkoordinate (UTM-Auszug)")

    format = st.selectbox("Koordinatenformat", ["4/4", "5/4"])
    ost = st.text_input("Ostwert", "7601")
    nord = st.text_input("Nordwert", "2467")

    def expand_coords(ost, nord, fmt):
        try:
            if fmt == "4/4":
                full_ost = int("57" + ost)
                full_nord = int("522" + nord)
            elif fmt == "5/4":
                full_ost = int(ost)
                full_nord = int("522" + nord)
            else:
                return None, None
            return full_ost, full_nord
        except:
            return None, None

    ziel_e, ziel_n = expand_coords(ost, nord, format)

    if ziel_e and ziel_n:
        try:
            lat, lon = utm.to_latlon(ziel_e, ziel_n, DEFAULT_ZONE_NUMBER, DEFAULT_ZONE_LETTER)
            st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
            st.success(f"Ziel (WGS84): {lat:.6f}, {lon:.6f}")
        except utm.error.OutOfRangeError:
            st.error("Koordinaten außerhalb gültiger UTM-Zone.")
    else:
        st.warning("Ungültige Koordinateneingabe.")

    if st.button("Zurück zur Startseite"):
        st.session_state.page = "Startseite"
        st.experimental_rerun()

main()
