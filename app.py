# HAB CompetitionBrain Kindermann-Schön – Version V1.7 – Flächenberechnung

import streamlit as st
import pandas as pd
import numpy as np
import io
from itertools import combinations
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull

st.set_page_config(page_title="HAB CompetitionBrain – Flächenanalyse V1.7")

st.title("📐 Größtmögliche Dreiecksfläche aus Winddaten")
st.caption("Version V1.7 – Ursprungsversion")

st.header("1) Winddaten eingeben")

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

if st.session_state.wind_df.empty:
    st.stop()

df = st.session_state.wind_df.copy()

st.header("2) Berechnung der maximalen Fläche")

# Umrechnung der Winddaten in Vektoren
def wind_to_vector(deg, kmh):
    rad = np.radians(deg)
    ms = kmh / 3.6
    return np.array([np.sin(rad) * ms, np.cos(rad) * ms])

vectors = []
heights = []

for _, row in df.iterrows():
    try:
        v = wind_to_vector(float(row["Richtung [°]"]), float(row["Geschwindigkeit [km/h]"]))
        vectors.append(v)
        heights.append(float(row["Höhe [ft]"]))
    except:
        continue

points = np.array(vectors)

def triangle_area(p1, p2, p3):
    return 0.5 * abs(np.cross(p2 - p1, p3 - p1))

top_areas = []

for i, j, k in combinations(range(len(points)), 3):
    a = triangle_area(points[i], points[j], points[k])
    top_areas.append((a, i, j, k))

top_areas.sort(reverse=True, key=lambda x: x[0])
top_5 = top_areas[:5]

st.subheader("Top 5 Flächenlösungen")

for idx, (area, i, j, k) in enumerate(top_5):
    st.markdown(f"**#{idx+1}** – Fläche: {area:.2f} (m²/s²) – Höhen: {heights[i]} / {heights[j]} / {heights[k]} ft")

st.subheader("Darstellung größter Fläche")

if top_5:
    _, i, j, k = top_5[0]
    fig, ax = plt.subplots()
    ax.quiver(0, 0, points[:,0], points[:,1], angles='xy', scale_units='xy', scale=1, color='lightgray')
    triangle = np.array([points[i], points[j], points[k], points[i]])
    ax.plot(triangle[:,0], triangle[:,1], 'r-o', label='Größte Fläche')
    ax.set_aspect('equal')
    ax.set_title("Windvektoren & größte Dreiecksfläche")
    ax.grid(True)
    st.pyplot(fig)
