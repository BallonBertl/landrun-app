# HAB CompetitionBrain Kindermann-Schön – Dreiecksflächenanalyse V1.7
import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial import ConvexHull
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="HAB CompetitionBrain Kindermann-Schön – Flächenanalyse")

if "wind_df" not in st.session_state:
    st.session_state.wind_df = pd.DataFrame(columns=["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"])

st.title("Flächenanalyse – Top 5 Dreiecke")
st.caption("Version 1.7 – Nur Flächenberechnung, ohne Koordinaten")

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
                st.success("Windprofil erfolgreich geladen.")
            else:
                st.error("Nicht genügend Spalten in der Datei.")
        except Exception as e:
            st.error(f"Fehler beim Einlesen der Datei: {e}")

with manual_col:
    st.write("Oder manuelle Eingabe:")
    st.session_state.wind_df = st.data_editor(
        st.session_state.wind_df,
        num_rows="dynamic",
        use_container_width=True
    )

df = st.session_state.wind_df
if df.empty:
    st.stop()

# Vektoren berechnen
punkte = []
for _, row in df.iterrows():
    try:
        richtung = float(row["Richtung [°]"])
        geschwindigkeit = float(row["Geschwindigkeit [km/h]"])
    except (ValueError, TypeError):
        continue
    rad = np.radians(richtung)
    vx = np.sin(rad) * geschwindigkeit
    vy = np.cos(rad) * geschwindigkeit
    punkte.append([vx, vy])

punkte = np.array(punkte)
if len(punkte) < 3:
    st.warning("Mindestens 3 gültige Vektoren erforderlich.")
    st.stop()

# Alle möglichen Dreiecke prüfen
from itertools import combinations
kombis = list(combinations(range(len(punkte)), 3))

def dreiecksfläche(a, b, c):
    return 0.5 * abs((a[0]*(b[1]-c[1]) + b[0]*(c[1]-a[1]) + c[0]*(a[1]-b[1])))

flächen = []
for i, j, k in kombis:
    A, B, C = punkte[i], punkte[j], punkte[k]
    fläche = dreiecksfläche(A, B, C)
    flächen.append((fläche, [A, B, C]))

flächen.sort(reverse=True, key=lambda x: x[0])
top5 = flächen[:5]

st.subheader("Top 5 Dreiecke nach Fläche")
for idx, (f, dreieck) in enumerate(top5, start=1):
    st.markdown(f"**#{idx}:** Fläche: {f:.2f} km²")

# Darstellung
fig, ax = plt.subplots()
ax.quiver(0, 0, punkte[:,0], punkte[:,1], angles='xy', scale_units='xy', scale=1, color='lightgray')
farben = ['red', 'green', 'blue', 'orange', 'purple']
for idx, (_, dreieck) in enumerate(top5):
    poly = np.array(dreieck + [dreieck[0]])  # zurück zum Startpunkt
    ax.plot(poly[:,0], poly[:,1], label=f"#{idx+1}", color=farben[idx])
ax.set_aspect('equal')
ax.set_title("Top 5 Flächen")
ax.grid(True)
ax.legend()
st.pyplot(fig)
