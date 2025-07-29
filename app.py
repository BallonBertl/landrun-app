
# HAB CompetitionBrain Kindermann-Schön – Top 5 Flächenberechnung
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations
from math import radians, sin, cos
import io

st.set_page_config(page_title="HAB CompetitionBrain Kindermann-Schön")

st.title("Top 5 Flächen – Zwei-Höhen-Taktik")
st.caption("🔧 Version 1.7 – Modifiziert mit manueller Eingabe & Dateiimport")

# Winddaten initialisieren
if "wind_df" not in st.session_state:
    st.session_state.wind_df = pd.DataFrame(columns=["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"])

# Eingabeoptionen
st.header("1) Winddaten eingeben")

col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("Winddatei hochladen (.txt oder .csv)", type=["txt", "csv"])
    if uploaded_file:
        try:
            lines = uploaded_file.read().decode("utf-8").splitlines()
            lines = [line for line in lines if not line.startswith("#") and line.strip() != ""]
            df = pd.read_csv(io.StringIO("\n".join(lines)), sep="\t", header=None)
            if df.shape[1] >= 3:
                df.columns = ["Höhe [ft]", "Richtung [°]", "Geschwindigkeit [km/h]"]
                st.session_state.wind_df = df
                st.success("Winddaten erfolgreich geladen.")
            else:
                st.error("Datei enthält zu wenige Spalten.")
        except Exception as e:
            st.error(f"Fehler beim Einlesen der Datei: {e}")

with col2:
    st.write("Oder manuelle Eingabe:")
    st.session_state.wind_df = st.data_editor(
        st.session_state.wind_df,
        num_rows="dynamic",
        use_container_width=True
    )

# Parameter
st.header("2) Einstellungen")

gesamtzeit_min = st.number_input("Maximale Gesamtzeit (Minuten)", min_value=1, value=5)
steigrate = st.number_input("Maximale Steig-/Sinkrate (m/s)", min_value=0.1, value=2.0)

# Berechnung starten
if st.button("Berechnen"):
    df = st.session_state.wind_df.copy()
    try:
        df = df.astype({"Höhe [ft]": float, "Richtung [°]": float, "Geschwindigkeit [km/h]": float})
    except:
        st.error("Bitte gültige numerische Werte eingeben.")
        st.stop()

    windvektoren = []
    for _, row in df.iterrows():
        richtung = radians(row["Richtung [°]"])
        geschwindigkeit = row["Geschwindigkeit [km/h]"] / 3.6
        vx = sin(richtung) * geschwindigkeit
        vy = cos(richtung) * geschwindigkeit
        windvektoren.append({"höhe": row["Höhe [ft]"], "vx": vx, "vy": vy, "v_kmh": row["Geschwindigkeit [km/h]"]})

    ergebnisse = []
    gesamtzeit_sec = gesamtzeit_min * 60

    for h1, h2 in combinations(windvektoren, 2):
        delta_h = abs(h1["höhe"] - h2["höhe"]) * 0.3048
        wechselzeit = delta_h / steigrate
        verbleibend = gesamtzeit_sec - wechselzeit
        if verbleibend <= 0:
            continue
        for t1_frac in np.linspace(0.1, 0.9, 9):
            t1 = verbleibend * t1_frac
            t2 = verbleibend - t1
            dx = h1["vx"] * t1 + h2["vx"] * t2
            dy = h1["vy"] * t1 + h2["vy"] * t2
            fläche = 0.5 * abs(dx * dy)
            ergebnisse.append({
                "Höhe 1": h1["höhe"],
                "v1": h1["v_kmh"],
                "t1": t1,
                "Höhe 2": h2["höhe"],
                "v2": h2["v_kmh"],
                "t2": t2,
                "Fläche": fläche
            })

    if not ergebnisse:
        st.warning("Keine gültigen Kombinationen gefunden.")
        st.stop()

    df_result = pd.DataFrame(ergebnisse)
    df_top5 = df_result.sort_values(by="Fläche", ascending=False).head(5).copy()

    def format_time(s):
        m = int(s // 60)
        sec = int(s % 60)
        return f"{m:02d}:{sec:02d}"

    df_top5["Zeit 1"] = df_top5["t1"].apply(format_time)
    df_top5["Zeit 2"] = df_top5["t2"].apply(format_time)

    df_display = df_top5[[
        "Höhe 1", "v1", "Zeit 1", "Höhe 2", "v2", "Zeit 2", "Fläche"
    ]].reset_index(drop=True)
    df_display.index += 1
    df_display.rename(columns={
        "v1": "Geschw. 1 [km/h]",
        "v2": "Geschw. 2 [km/h]",
        "Fläche": "Fläche [km²]"
    }, inplace=True)

    st.header("3) Top 5 Ergebnisse")
    st.dataframe(df_display.style.format(precision=2), use_container_width=True)

    st.header("4) Visualisierung")
    auswahl = st.selectbox("Variante auswählen", options=list(df_display.index), format_func=lambda x: f"Variante {x}")
    selected = df_top5.iloc[auswahl - 1]

    punkte = np.array([
        [0, 0],
        [selected["vx"] * selected["t1"], selected["vy"] * selected["t1"]],
        [selected["vx"] * selected["t1"] + selected["vx"] * selected["t2"],
         selected["vy"] * selected["t1"] + selected["vy"] * selected["t2"]]
    ])

    fig, ax = plt.subplots()
    ax.plot(punkte[:, 0], punkte[:, 1], marker="o")
    ax.set_aspect("equal")
    ax.set_title("Bewegungspfad")
    ax.grid(True)
    st.pyplot(fig)
