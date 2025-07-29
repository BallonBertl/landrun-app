# HAB CompetitionBrain Kindermann-Schön – Version Fläche 1.0
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull

st.set_page_config(page_title="HAB CompetitionBrain – Flächenanalyse", layout="centered")

st.title("Größtmögliche Dreiecksfläche aus Windvektoren")
st.caption("Version Fläche 1.0 – Basierend auf V1.7")

st.header("1) Windprofil eingeben")
upload_col, manual_col = st.columns(2)

if "wind_df" not in st.session_state:
    st.session_state.wind_df = pd.DataFrame(columns=["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"])

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

df = st.session_state.wind_df
if df.empty:
    st.warning("Bitte Winddaten eingeben oder hochladen.")
    st.stop()

# Umrechnung in Windvektoren
points = []
triples = []
for _, row in df.iterrows():
    try:
        deg = float(row["Richtung [°]"])
        spd_kmh = float(row["Geschwindigkeit [km/h]"])
    except:
        continue
    spd_ms = spd_kmh / 3.6
    dir_rad = np.radians(deg)
    x = np.sin(dir_rad) * spd_ms
    y = np.cos(dir_rad) * spd_ms
    points.append([x, y])
points = np.array(points)

# Berechnung größtmöglicher Dreiecksfläche
max_area = 0
best_combo = None
n = len(points)
for i in range(n):
    for j in range(i+1, n):
        for k in range(j+1, n):
            a = points[i]
            b = points[j]
            c = points[k]
            area = 0.5 * abs(np.cross(b - a, c - a))
            if area > max_area:
                max_area = area
                best_combo = (a, b, c)

if best_combo:
    st.header("2) Ergebnis")
    st.success(f"Größte Fläche: {max_area:.2f} m²")

    fig, ax = plt.subplots()
    ax.quiver(np.zeros(len(points)), np.zeros(len(points)), points[:,0], points[:,1], angles='xy', scale_units='xy', scale=1, color='lightgray')
    ax.set_xlabel("x (m/s)")
    ax.set_ylabel("y (m/s)")
    ax.set_title("Windvektoren und größte Fläche")
    ax.set_aspect("equal")

    triangle = np.array(best_combo + (best_combo[0],))  # Zurück zum Startpunkt
    ax.plot(triangle[:,0], triangle[:,1], 'r-', lw=2)
    st.pyplot(fig)
else:
    st.warning("Nicht genügend gültige Daten für Flächenberechnung.")
