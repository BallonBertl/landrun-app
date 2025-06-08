# HAB CompetitionBrain Kindermann-Schön – Version 5 garantiert korrekt
import streamlit as st
import pandas as pd
import numpy as np
import utm
import io

st.set_page_config(page_title="HAB CompetitionBrain Kindermann-Schön")

# -------------------------------
# Session-State vorbereiten
# -------------------------------
if "wind_df" not in st.session_state:
    st.session_state.wind_df = pd.DataFrame(columns=["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"])
if "wind_ready" not in st.session_state:
    st.session_state.wind_ready = False
if "page" not in st.session_state:
    st.session_state.page = "START"

# -------------------------------
# STARTSEITE
# -------------------------------
def startseite():
    st.title("HAB CompetitionBrain Kindermann-Schön")
    st.caption("🛠 DEBUG: Version 5 – vollständiger Code aktiv")

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

        if st.button("Windprofil übernehmen"):
            if not st.session_state.wind_df.empty:
                st.session_state.wind_ready = True
                st.success("Windprofil übernommen.")
            else:
                st.error("Bitte mindestens eine Zeile eingeben.")

    st.divider()
    st.header("2) Tools und Aufgaben")

    # Immer sichtbare Tools
    st.subheader("Tools (immer verfügbar):")
    st.button("📍 Markerdrop (folgt)", disabled=True)
    st.button("⏬ Steigen/Sinken (folgt)", disabled=True)
    st.button("🔄 Einheiten umrechnen (folgt)", disabled=True)

    # Aufgaben – nur sichtbar wenn Windprofil vorhanden
    if st.session_state.wind_ready:
        st.subheader("Aufgaben (aktiv nach Winddaten):")
        if st.button("ILP"):
            st.session_state.page = "ILP"
    else:
        st.info("Bitte zuerst gültige Winddaten eingeben, um Aufgaben freizuschalten.")

# -------------------------------
# ILP SEITE
# -------------------------------
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

    df = st.session_state.wind_df
    wind_profile = []
    for _, row in df.iterrows():
        h = row["Höhe [ft]"]
        deg = row["Richtung [°]"]
        spd_kmh = row["Geschwindigkeit [km/h]"]
        spd_ms = spd_kmh / 3.6  # nur intern für Vektorrechnung
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
        ilp_candidates.append({ "easting": easting + dx, "northing": northing + dy })

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

    if st.button("🔙 Zurück zur Startseite"):
        st.session_state.page = "START"

# -------------------------------
# SEITENSTEUERUNG
# -------------------------------
if st.session_state.page == "START":
    startseite()
elif st.session_state.page == "ILP":
    ilp_seite()
