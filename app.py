# HAB CompetitionBrain Kindermann-Schön – Dreiecksflächenanalyse V1.7
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
import io

st.set_page_config(page_title="HAB CompetitionBrain – Dreiecksflächen")

st.title("Größtmögliche Dreiecksflächen – V1.7")
st.caption("🔺 Analyse basierend auf Winddaten")

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
            df = pd.read_csv(io.StringIO("\n".join(data_lines)), sep="\t", header=None)
            if df.shape[1] >= 3:
                df.columns = ["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"]
                st.session_state.wind_df = df
                st.success("Winddaten erfolgreich geladen.")
            else:
                st.error("Nicht genügend Spalten gefunden.")
        except Exception as e:
            st.error(f"Fehler beim Einlesen der Datei: {e}")

with manual_col:
    st.write("Oder manuelle Eingabe:")
    st.session_state.wind_df = st.data_editor(
        st.session_state.wind_df,
        num_rows="dynamic",
        use_container_width=True
    )

if not st.session_state.wind_df.empty:
    st.divider()
    st.header("2) Größtmögliche Dreiecksflächen berechnen")

    df = st.session_state.wind_df.copy()
    df.dropna(inplace=True)

    # Umwandlung in Vektoren
    vectors = []
    for _, row in df.iterrows():
        deg = float(row["Richtung [°]"])
        spd_kmh = float(row["Geschwindigkeit [km/h]"])
        spd_ms = spd_kmh / 3.6
        rad = np.radians(deg)
        x = np.sin(rad) * spd_ms
        y = np.cos(rad) * spd_ms
        vectors.append([x, y])

    points = np.array(vectors)

    if len(points) < 3:
        st.warning("Mindestens 3 gültige Windschichten erforderlich.")
    else:
        hull = ConvexHull(points)
        max_area = 0
        best_triangles = []

        # Alle möglichen Dreiecke auf der Hülle testen
        for i in range(len(hull.vertices)):
            for j in range(i + 1, len(hull.vertices)):
                for k in range(j + 1, len(hull.vertices)):
                    a = points[hull.vertices[i]]
                    b = points[hull.vertices[j]]
                    c = points[hull.vertices[k]]
                    area = 0.5 * np.abs((a[0]*(b[1]-c[1]) + b[0]*(c[1]-a[1]) + c[0]*(a[1]-b[1])))
                    best_triangles.append((area, [a, b, c]))

        best_triangles.sort(reverse=True, key=lambda x: x[0])
        top5 = best_triangles[:5]

        st.subheader("📊 Top 5 Flächen (in m²):")
        for idx, (area, triangle) in enumerate(top5, start=1):
            st.write(f"{idx}. Fläche: {area:.2f} m²")

        # Plotten
        st.subheader("📉 Darstellung der größten Fläche")
        fig, ax = plt.subplots()
        ax.set_title("Windvektoren und größtes Dreieck")
        ax.set_xlabel("x [m/s]")
        ax.set_ylabel("y [m/s]")
        ax.grid(True)
        ax.quiver(0, 0, points[:, 0], points[:, 1], angles='xy', scale_units='xy', scale=1, color='lightgray')

        # größtes Dreieck visualisieren
        largest = top5[0][1]
        poly = np.array(largest + [largest[0]])  # zurück zum Startpunkt
        ax.plot(poly[:, 0], poly[:, 1], 'r-', linewidth=2)
        ax.fill(poly[:, 0], poly[:, 1], 'red', alpha=0.3)

        st.pyplot(fig)
