import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations

st.set_page_config(page_title="Dreiecksfläche – CompetitionBrain", layout="centered")

st.title("Größtmögliche Dreiecksfläche aus zwei Höhen")

# Eingabe: Winddaten (manuell oder Datei)
st.subheader("Winddaten eingeben")

example_df = pd.DataFrame({
    "Höhe [ft]": [1000, 2000, 3000, 4000, 5000],
    "Richtung [°]": [90, 135, 180, 225, 270],
    "Geschwindigkeit [km/h]": [10, 20, 30, 40, 50]
})

tab1, tab2 = st.tabs(["Manuelle Eingabe", "Datei-Upload"])
with tab1:
    wind_df = st.data_editor(example_df, num_rows="dynamic", use_container_width=True)
with tab2:
    uploaded_file = st.file_uploader("Winddaten als .csv oder .txt", type=["csv", "txt"])
    if uploaded_file is not None:
        try:
            wind_df = pd.read_csv(uploaded_file, sep=None, engine="python")
            st.success("Datei erfolgreich geladen")
        except Exception as e:
            st.error(f"Fehler beim Einlesen der Datei: {e}")

if wind_df.empty:
    st.stop()

# Eingaben: Maximalzeit und Steig-/Sinkrate
st.subheader("Berechnungsparameter")
max_time_min = st.number_input("Maximale Gesamtzeit (Minuten)", min_value=1, value=10)
climb_rate = st.number_input("Steig-/Sinkrate (m/s)", min_value=0.1, value=2.0, step=0.1)

# Umrechnung der Winddaten in Vektoren
wind_vectors = []
for _, row in wind_df.iterrows():
    try:
        height = float(row["Höhe [ft]"])
        direction = float(row["Richtung [°]"])
        speed_kmh = float(row["Geschwindigkeit [km/h]"])
    except:
        continue
    speed_ms = speed_kmh / 3.6
    angle_rad = np.radians(direction)
    dx = np.sin(angle_rad) * speed_ms
    dy = np.cos(angle_rad) * speed_ms
    wind_vectors.append({
        "höhe": height,
        "geschw_kmh": speed_kmh,
        "vector": np.array([dx, dy])
    })

# Berechnung möglicher Flächen mit zwei Höhenkombinationen
results = []
for h1, h2 in combinations(wind_vectors, 2):
    h_diff = abs(h1["höhe"] - h2["höhe"]) * 0.3048
    t_climb = h_diff / climb_rate
    time_left = max_time_min * 60 - t_climb
    if time_left <= 0:
        continue

    for t1_frac in np.linspace(0.1, 0.9, 9):
        t1 = time_left * t1_frac
        t2 = time_left - t1

        p1 = h1["vector"] * t1
        p2 = h2["vector"] * t2

        # Dreiecksfläche berechnen (2D)
        area = 0.5 * np.abs(np.cross(p1, p2))

        results.append({
            "höhe1": h1["höhe"],
            "geschw1": h1["geschw_kmh"],
            "zeit1": t1,
            "höhe2": h2["höhe"],
            "geschw2": h2["geschw_kmh"],
            "zeit2": t2,
            "fläche": area,
            "p1": p1,
            "p2": p2
        })

if not results:
    st.warning("Keine gültige Kombination gefunden.")
    st.stop()

# Top 5 Ergebnisse
sorted_results = sorted(results, key=lambda x: x["fläche"], reverse=True)[:5]

# Auswahl zur Visualisierung
auswahl = st.selectbox("Variante zur Visualisierung wählen (Rang)", list(range(1, len(sorted_results)+1)))
auswahl_idx = auswahl - 1

# Tabelle anzeigen
st.subheader("Top 5 Ergebnisse")
data = []
for i, res in enumerate(sorted_results, 1):
    mm1, ss1 = divmod(int(res["zeit1"]), 60)
    mm2, ss2 = divmod(int(res["zeit2"]), 60)
    data.append([
        i,
        int(res["höhe1"]), f"{res['geschw1']:.1f} km/h", f"{mm1:02}:{ss1:02}",
        int(res["höhe2"]), f"{res['geschw2']:.1f} km/h", f"{mm2:02}:{ss2:02}",
        f"{res['fläche']:.0f} m²"
    ])

st.table(pd.DataFrame(data, columns=["Rang", "Höhe 1", "Geschw. 1", "Zeit 1", "Höhe 2", "Geschw. 2", "Zeit 2", "Fläche"]))

# Visualisierung der gewählten Variante
res = sorted_results[auswahl_idx]
p1 = res["p1"]
p2 = res["p2"]

fig, ax = plt.subplots()
ax.quiver(0, 0, p1[0], p1[1], angles='xy', scale_units='xy', scale=1, color='red', label="Höhe 1")
ax.quiver(0, 0, p2[0], p2[1], angles='xy', scale_units='xy', scale=1, color='blue', label="Höhe 2")
ax.quiver(0, 0, p1[0]+p2[0], p1[1]+p2[1], angles='xy', scale_units='xy', scale=1, color='green', label="Resultierende")
ax.set_xlim(-5000, 5000)
ax.set_ylim(-5000, 5000)
ax.set_aspect('equal')
ax.grid(True)
ax.set_title(f"Visualisierung – Variante Rang {auswahl}")
ax.legend()
st.pyplot(fig)
