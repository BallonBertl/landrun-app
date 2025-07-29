# HAB CompetitionBrain – Flächenoptimierung v1.7.3
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations
from math import radians, sin, cos

st.set_page_config(page_title="HAB CompetitionBrain – Flächenoptimierung")

st.title("🔺 Größtmögliche Fläche mit zwei Höhen")
st.caption("Version 1.7.3 – mit Zeit/Steigrate, manuelle Eingabe + Dateiimport")

# SessionState initialisieren
if "wind_df" not in st.session_state:
    st.session_state.wind_df = pd.DataFrame(columns=["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"])

st.header("1) Winddaten eingeben")

upload_col, manual_col = st.columns(2)

with upload_col:
    uploaded_file = st.file_uploader("Winddatei hochladen (.txt oder .csv)", type=["txt", "csv"])
    if uploaded_file is not None:
        try:
            lines = uploaded_file.read().decode("utf-8").splitlines()
            data_lines = [line for line in lines if not line.startswith("#") and line.strip() != ""]
            df = pd.read_csv(pd.compat.StringIO("\n".join(data_lines)), sep="\t", header=None)
            if df.shape[1] >= 3:
                df.columns = ["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"]
                st.session_state.wind_df = df
                st.success("Datei erfolgreich geladen.")
            else:
                st.error("Datei hat nicht genügend Spalten.")
        except Exception as e:
            st.error(f"Fehler beim Einlesen der Datei: {e}")

with manual_col:
    st.write("Oder manuelle Eingabe:")
    st.session_state.wind_df = st.data_editor(
        st.session_state.wind_df,
        num_rows="dynamic",
        use_container_width=True
    )

if st.session_state.wind_df.empty:
    st.warning("Bitte Winddaten eingeben oder importieren.")
    st.stop()

st.header("2) Einstellungen")

max_time_min = st.slider("Maximale Gesamtzeit (Minuten)", min_value=1, max_value=60, value=30)
rate = st.slider("Steig-/Sinkrate (m/s)", min_value=0.5, max_value=10.0, value=5.0, step=0.1)

# Umrechnung
max_time_sec = max_time_min * 60
wind_df = st.session_state.wind_df.copy()

# Umrechnen in Vektoren
wind_vectors = []
for _, row in wind_df.iterrows():
    try:
        h = float(row["Höhe [ft]"])
        deg = float(row["Richtung [°]"])
        spd_kmh = float(row["Geschwindigkeit [km/h]"])
        spd_ms = spd_kmh / 3.6
        dir_rad = radians(deg)
        vec = np.array([sin(dir_rad) * spd_ms, cos(dir_rad) * spd_ms])
        wind_vectors.append((h, vec, spd_kmh))
    except:
        continue

if len(wind_vectors) < 2:
    st.error("Mindestens zwei gültige Höhen erforderlich.")
    st.stop()

# Kombinationen prüfen
resultate = []
for (h1, v1, kmh1), (h2, v2, kmh2) in combinations(wind_vectors, 2):
    dh = abs(h2 - h1) * 0.3048
    switch_time = dh / rate
    rest_time = max_time_sec - switch_time
    if rest_time <= 0:
        continue
    for t1_frac in np.linspace(0.01, 0.99, 20):
        t1 = rest_time * t1_frac
        t2 = rest_time - t1
        p1 = v1 * t1
        p2 = v2 * t2
        area = 0.5 * abs(p1[0]*p2[1] - p1[1]*p2[0])
        resultate.append({
            "H1": int(h1),
            "V1": round(kmh1),
            "T1": t1,
            "H2": int(h2),
            "V2": round(kmh2),
            "T2": t2,
            "A": area
        })

if not resultate:
    st.warning("Keine gültigen Kombinationen gefunden.")
    st.stop()

# Top 5
df = pd.DataFrame(resultate)
df_sorted = df.sort_values(by="A", ascending=False).head(5).copy()

def fmt_time(sec):
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m:02d}:{s:02d}"

df_sorted["T1_fmt"] = df_sorted["T1"].apply(fmt_time)
df_sorted["T2_fmt"] = df_sorted["T2"].apply(fmt_time)

df_show = df_sorted[["H1", "V1", "T1_fmt", "H2", "V2", "T2_fmt", "A"]].copy()
df_show.columns = ["Höhe 1", "Geschw. 1", "Zeit 1", "Höhe 2", "Geschw. 2", "Zeit 2", "Fläche"]
st.subheader("3) Top 5 Flächen")
st.dataframe(df_show, use_container_width=True)

# Visualisierung
st.subheader("4) Visualisierung")
idx = st.selectbox("Variante wählen", options=range(len(df_sorted)), format_func=lambda i: f"Variante {i+1}")
v = df_sorted.iloc[idx]

# Punkte berechnen
dir1 = [sin(radians(vv)) for vv in [v["V1"]]*2]
dir2 = [cos(radians(vv)) for vv in [v["V1"]]*2]

vec1 = np.array([sin(radians(v["V1"])) * v["T1"] / 3.6, cos(radians(v["V1"])) * v["T1"] / 3.6])
vec2 = np.array([sin(radians(v["V2"])) * v["T2"] / 3.6, cos(radians(v["V2"])) * v["T2"] / 3.6])

p1 = np.array([0, 0])
p2 = p1 + vec1
p3 = p2 + vec2

punkte = np.array([p1, p2, p3])

fig, ax = plt.subplots(figsize=(5, 5))
ax.plot(punkte[:, 0], punkte[:, 1], marker='o')
ax.fill(punkte[:, 0], punkte[:, 1], alpha=0.2)
ax.set_title("Bewegungspfad")
ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")
ax.grid(True)
ax.axis("equal")
st.pyplot(fig)
