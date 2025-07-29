# HAB CompetitionBrain Kindermann-Schön – Version V1.7 (nur größte Dreiecksfläche)
import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial import ConvexHull
import matplotlib.pyplot as plt

st.set_page_config(page_title="HAB CompetitionBrain Kindermann-Schön – V1.7")

st.title("HAB CompetitionBrain Kindermann-Schön")
st.caption("🔺 Version V1.7 – Größtmögliche Dreiecksfläche aus Windvektoren")

st.header("1) Windprofil eingeben")
uploaded_file = st.file_uploader("Winddatei hochladen (.txt oder .csv)", type=["txt", "csv"])

if "wind_df" not in st.session_state:
    st.session_state.wind_df = pd.DataFrame(columns=["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"])

with st.expander("Oder manuelle Eingabe"):
    st.session_state.wind_df = st.data_editor(
        st.session_state.wind_df,
        num_rows="dynamic",
        use_container_width=True
    )

df = st.session_state.wind_df

if uploaded_file is not None:
    try:
        lines = uploaded_file.read().decode("utf-8").splitlines()
        data_lines = [line for line in lines if not line.startswith("#") and line.strip() != ""]
        df = pd.read_csv(pd.compat.StringIO("\n".join(data_lines)), sep="\t", header=None)
        if df.shape[1] >= 3:
            df.columns = ["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"]
            st.session_state.wind_df = df
    except Exception as e:
        st.error(f"Fehler beim Einlesen der Datei: {e}")

if df.empty:
    st.info("Bitte Winddaten eingeben.")
else:
    st.subheader("2) Größte Dreiecksfläche berechnen")

    wind_vectors = []
    for _, row in df.iterrows():
        try:
            deg = float(row["Richtung [°]"])
            spd_kmh = float(row["Geschwindigkeit [km/h]"])
            spd_ms = spd_kmh / 3.6
            dir_rad = np.radians(deg)
            wind_vector = [np.sin(dir_rad) * spd_ms, np.cos(dir_rad) * spd_ms]
            wind_vectors.append(wind_vector)
        except:
            continue

    if len(wind_vectors) < 3:
        st.warning("Mindestens drei gültige Windvektoren erforderlich.")
    else:
        points = np.array(wind_vectors)
        hull = ConvexHull(points)
        max_area = 0
        best_triangle = None

        for i in range(len(hull.vertices)):
            for j in range(i+1, len(hull.vertices)):
                for k in range(j+1, len(hull.vertices)):
                    a = points[hull.vertices[i]]
                    b = points[hull.vertices[j]]
                    c = points[hull.vertices[k]]
                    area = 0.5 * abs((a[0]*(b[1]-c[1]) + b[0]*(c[1]-a[1]) + c[0]*(a[1]-b[1])))
                    if area > max_area:
                        max_area = area
                        best_triangle = (a, b, c)

        st.success(f"Größte Dreiecksfläche: {max_area:.2f} m²/s²")

        fig, ax = plt.subplots()
        ax.quiver(0, 0, points[:,0], points[:,1], angles='xy', scale_units='xy', scale=1, color='lightgray')
        if best_triangle:
            tri = np.array(best_triangle + (best_triangle[0],))
            ax.plot(tri[:,0], tri[:,1], 'r-o', label="Größtes Dreieck")
        ax.set_title("Windvektoren und größtes Dreieck")
        ax.set_xlabel("x [m/s]")
        ax.set_ylabel("y [m/s]")
        ax.axis("equal")
        ax.grid(True)
        st.pyplot(fig)
