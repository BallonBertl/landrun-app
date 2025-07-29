# HAB CompetitionBrain Kindermann-Schön – v1.7.1 (Top-5 Dreiecksflächen)
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
from itertools import combinations
import io

st.set_page_config(page_title="HAB CompetitionBrain Kindermann-Schön – v1.7.1")
st.title("🏁 Größte Dreiecksflächen – Windvektoren")
st.caption("Version 1.7.1 – Nur Flächenberechnung, keine Koordinaten")

# Eingabe: Datei oder manuell
st.header("1) Winddaten eingeben")
upload_col, manual_col = st.columns(2)

def read_wind_file(uploaded_file):
    try:
        lines = uploaded_file.read().decode("utf-8").splitlines()
        lines = [line for line in lines if not line.startswith("#") and line.strip() != ""]
        df = pd.read_csv(io.StringIO("\n".join(lines)), sep="\t", header=None)
        df.columns = ["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"]
        return df
    except Exception as e:
        st.error(f"Fehler beim Einlesen der Datei: {e}")
        return pd.DataFrame(columns=["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"])

with upload_col:
    uploaded_file = st.file_uploader("Winddatei (.txt/.csv)", type=["txt", "csv"])
    if uploaded_file:
        wind_df = read_wind_file(uploaded_file)
    else:
        wind_df = pd.DataFrame(columns=["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"])

with manual_col:
    st.write("Oder manuelle Eingabe der Winddaten:")
    wind_df = st.data_editor(wind_df, num_rows="dynamic", use_container_width=True)

if wind_df.empty:
    st.warning("Bitte Winddaten eingeben, um Berechnung zu starten.")
    st.stop()

# Umrechnung in Vektoren
punkte = []
for _, row in wind_df.iterrows():
    try:
        richtung = float(row["Richtung [°]"])
        geschw = float(row["Geschwindigkeit [km/h]"]) / 3.6  # in m/s
        winkel_rad = np.radians(richtung)
        x = np.sin(winkel_rad) * geschw
        y = np.cos(winkel_rad) * geschw
        punkte.append([x, y])
    except:
        continue

punkte = np.array(punkte)
if len(punkte) < 3:
    st.warning("Mindestens 3 gültige Winddaten notwendig.")
    st.stop()

# Größte Dreiecksflächen berechnen
st.header("2) Größte Flächenkombinationen")

def dreiecksfläche(a, b, c):
    return 0.5 * abs((a[0]*(b[1]-c[1]) + b[0]*(c[1]-a[1]) + c[0]*(a[1]-b[1])))

kombis = list(combinations(punkte, 3))
flächen = [(dreiecksfläche(a, b, c), [a, b, c]) for a, b, c in kombis]
flächen.sort(reverse=True, key=lambda x: x[0])

st.subheader("Top 5 Flächenkombinationen (in m²)")
for i, (area, triangle) in enumerate(flächen[:5], 1):
    st.write(f"**#{i}** – Fläche: {area:.2f} m²")

# Visualisierung
st.header("3) Darstellung der größten Fläche")
beste_dreieck = flächen[0][1]
fig, ax = plt.subplots()

# Alle Vektoren als Pfeile vom Ursprung
for p in punkte:
    ax.quiver(0, 0, p[0], p[1], angles='xy', scale_units='xy', scale=1, color='lightgray', alpha=0.5)

# Bestes Dreieck zeichnen
dreieck_array = np.array(beste_dreieck + [beste_dreieck[0]])
ax.plot(dreieck_array[:,0], dreieck_array[:,1], 'b-o', label="Größtes Dreieck")
ax.fill(dreieck_array[:,0], dreieck_array[:,1], 'lightblue', alpha=0.5)

ax.set_aspect('equal')
ax.grid(True)
ax.set_title("Darstellung des größten Dreiecks")
ax.set_xlabel("x (m/s)")
ax.set_ylabel("y (m/s)")
ax.legend()
st.pyplot(fig)
