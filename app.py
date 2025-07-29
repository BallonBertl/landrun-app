
# HAB CompetitionBrain – Dreiecksfläche v1.7 (vereinfacht)
import streamlit as st
import pandas as pd
import numpy as np
import io
from scipy.spatial import ConvexHull
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dreiecksfläche – v1.7 einfach")

st.title("📐 Größtmögliche Dreiecksfläche – Version 1.7 einfach")
st.caption("Berechnet aus Winddaten mögliche Flächen für strategische Ballonstarts.")

# Winddaten laden oder manuell eingeben
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
                st.error("Nicht genügend Spalten gefunden.")
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
    st.warning("Bitte Winddaten hochladen oder manuell eingeben.")
    st.stop()

# Startpunkt (0/0) und Einstellungen
st.header("2) Einstellungen")
min_height, max_height = st.slider("Höhenbereich (ft)", 0, 10000, (0, 3000), step=100)
rate_limit = st.slider("Maximale Steig-/Sinkrate (m/s)", 0.5, 8.0, 2.0, step=0.5)

# Konvertierung & Berechnung
st.header("3) Berechnung")

wind_vectors = []
for _, row in df.iterrows():
    try:
        h_ft = float(row["Höhe [ft]"])
        if not (min_height <= h_ft <= max_height):
            continue
        deg = float(row["Richtung [°]"])
        spd_kmh = float(row["Geschwindigkeit [km/h]"])
        spd_ms = spd_kmh / 3.6
        dir_rad = np.radians(deg)
        vx = np.sin(dir_rad) * spd_ms
        vy = np.cos(dir_rad) * spd_ms
        t = (2 * h_ft * 0.3048) / rate_limit
        dx = vx * t
        dy = vy * t
        wind_vectors.append((dx, dy))
    except:
        continue

if len(wind_vectors) < 3:
    st.error("Nicht genügend gültige Windvektoren zur Flächenberechnung.")
    st.stop()

# Alle möglichen Dreiecke und Flächen berechnen
punkte = np.array(wind_vectors)
kombis = []
n = len(punkte)
for i in range(n):
    for j in range(i + 1, n):
        for k in range(j + 1, n):
            a, b, c = punkte[i], punkte[j], punkte[k]
            area = 0.5 * abs(np.cross(b - a, c - a))
            kombis.append({"punkte": (a, b, c), "fläche": area})

top5 = sorted(kombis, key=lambda x: x["fläche"], reverse=True)[:5]

st.subheader("Top 5 Flächenkombinationen")
for i, combo in enumerate(top5, 1):
    a, b, c = combo["punkte"]
    st.markdown(f"**#{i}:** Fläche: {combo['fläche']:.2f} km²")

# Visualisierung
st.subheader("Visualisierung größter Fläche")
fig, ax = plt.subplots()
a, b, c = top5[0]["punkte"]
triangle = np.array([a, b, c, a])
ax.plot(triangle[:, 0], triangle[:, 1], 'bo-')
ax.set_title("Größte Dreiecksfläche")
ax.set_xlabel("Entfernung X [m]")
ax.set_ylabel("Entfernung Y [m]")
ax.grid(True)
ax.axis("equal")
st.pyplot(fig)
