# HAB CompetitionBrain Kindermann-Schön – Triangle Area Tool – V1.8
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
import io

st.set_page_config(page_title="Triangle Area Tool – V1.8")

if "wind_df" not in st.session_state:
    st.session_state.wind_df = pd.DataFrame(columns=["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"])

st.title("Größtmögliche Fläche mit zwei Höhen – V1.8")

# Eingabe: Windprofil
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

# Eingaben: Max Zeit und Steig-/Sinkrate
st.header("2) Einstellungen")
max_zeit_min = st.number_input("Maximale Gesamtzeit (min)", min_value=1, max_value=60, value=10)
steigrate = st.number_input("Maximale Steig-/Sinkrate (m/s)", min_value=0.1, max_value=10.0, value=2.0, step=0.1)

# Berechnung
st.header("3) Größtmögliche Fläche berechnen")

def berechne_flaechen(wind_df, max_zeit_s, steigrate):
    punkte = []
    for _, row in wind_df.iterrows():
        try:
            hoehe = float(row["Höhe [ft]"])
            richtung = float(row["Richtung [°]"])
            speed_kmh = float(row["Geschwindigkeit [km/h]"])
        except:
            continue
        speed_ms = speed_kmh / 3.6
        dir_rad = np.radians(richtung)
        dx = np.sin(dir_rad) * speed_ms
        dy = np.cos(dir_rad) * speed_ms
        punkte.append((hoehe, dx, dy))
    
    resultate = []
    for i in range(len(punkte)):
        for j in range(i+1, len(punkte)):
            h1, dx1, dy1 = punkte[i]
            h2, dx2, dy2 = punkte[j]
            dh = abs(h2 - h1) * 0.3048  # ft to m
            zeitwechsel = dh / steigrate
            verbleibend = max_zeit_s - zeitwechsel
            if verbleibend <= 0:
                continue
            t1 = t2 = verbleibend / 2
            p1 = np.array([dx1 * t1, dy1 * t1])
            p2 = np.array([dx2 * t2, dy2 * t2])
            flaeche = 0.5 * np.abs(p1[0]*p2[1] - p2[0]*p1[1])
            resultate.append({
                "Höhe 1 [ft]": int(h1),
                "Zeit 1": t1,
                "Höhe 2 [ft]": int(h2),
                "Zeit 2": t2,
                "Fläche [km²]": flaeche / 1e6,
                "Punkte": [(0, 0), tuple(p1), tuple(p1 + p2)]
            })

    resultate.sort(key=lambda x: x["Fläche [km²]"], reverse=True)
    return resultate[:5]

if not st.session_state.wind_df.empty:
    max_zeit_s = max_zeit_min * 60
    top5 = berechne_flaechen(st.session_state.wind_df, max_zeit_s, steigrate)
    if top5:
        st.subheader("Top 5 Flächen")
        for idx, eintrag in enumerate(top5, 1):
            z1 = f"{int(eintrag['Zeit 1']//60):02d}:{int(eintrag['Zeit 1']%60):02d}"
            z2 = f"{int(eintrag['Zeit 2']//60):02d}:{int(eintrag['Zeit 2']%60):02d}"
            st.markdown(f"**{idx}.** {eintrag['Höhe 1 [ft]']} ft ({z1}) → {eintrag['Höhe 2 [ft]']} ft ({z2}) → Fläche: {eintrag['Fläche [km²]']:.2f} km²")

        st.subheader("Visualisierung")
        fig, ax = plt.subplots()
        for eintrag in top5:
            p = np.array(eintrag["Punkte"])
            ax.plot(p[:,0], p[:,1], marker="o")
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_title("Top 5 Flächen (2 Schenkel)")
        ax.grid(True)
        ax.axis("equal")
        st.pyplot(fig)
    else:
        st.warning("Keine gültige Kombination gefunden.")
else:
    st.info("Bitte zuerst Winddaten eingeben.")
