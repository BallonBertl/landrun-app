import streamlit as st
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
from itertools import combinations
import re
import concurrent.futures

st.set_page_config(page_title="Land Run Auswertung", layout="centered")
st.title("🏁 Land Run Auswertung")
st.markdown("Berechne die optimale Höhenstrategie zur Maximierung der Dreiecksfläche.")

mode = st.radio("🌀 Wie möchtest du Winddaten eingeben?", ["Datei hochladen", "Manuell eingeben"])
df = None

if mode == "Datei hochladen":
    uploaded_file = st.file_uploader("📤 Winddaten (.csv, .txt)", type=["csv", "txt"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".txt"):
                txt_content = uploaded_file.read().decode("utf-8", errors="ignore")
                lines = txt_content.strip().splitlines()[1:]  # erste Zeile überspringen
                data = []
                for line in lines:
                    parts = re.split(r"[\t\s]+", line.strip())
                    if len(parts) == 3:
                        data.append([float(p) for p in parts])
                df = pd.DataFrame(data, columns=["Altitude_ft", "Direction_deg", "Speed_kmh"])
            else:
                df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Fehler beim Einlesen der Datei: {e}")
elif mode == "Manuell eingeben":
    default_data = pd.DataFrame({
        'Altitude_ft': [0, 1000, 2000, 3000],
        'Direction_deg': [0, 45, 90, 135],
        'Speed_kmh': [10, 15, 20, 25]
    })
    raw_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)
    try:
        df = raw_df.dropna()
        df = df.astype({'Altitude_ft': float, 'Direction_deg': float, 'Speed_kmh': float})
        if df.empty:
            st.warning("⚠️ Keine gültigen Winddaten eingegeben.")
            df = None
    except Exception as e:
        st.error(f"❌ Fehlerhafte Eingaben erkannt: {e}")
        df = None

col1, col2 = st.columns(2)
with col1:
    flight_time_min = st.number_input("Flugdauer [min]", min_value=5, max_value=90, value=30, step=5)
with col2:
    climb_rate = st.number_input("Steig-/Sinkrate [m/s]", min_value=0.1, max_value=10.0, value=4.0, step=0.1)

def simulate_landrun_fast_parallel(df, duration_sec, climb_rate):
    altitudes = df['Altitude_ft'].unique()
    altitudes.sort()
    results = []

    interp_dirs = {alt: np.interp(alt, df['Altitude_ft'], df['Direction_deg']) for alt in altitudes}
    interp_speeds = {alt: np.interp(alt, df['Altitude_ft'], df['Speed_kmh']) for alt in altitudes}
    wind_vectors = {}
    for alt in altitudes:
        dir_rad = math.radians(interp_dirs[alt])
        speed_ms = interp_speeds[alt] / 3.6
        dx = speed_ms * math.sin(dir_rad)
        dy = speed_ms * math.cos(dir_rad)
        wind_vectors[alt] = np.array([dx, dy])

    combos = [(h1, h2) for h1, h2 in combinations(altitudes, 2)
              if (duration_sec - abs(h2 - h1) * 0.3048 / climb_rate) > 0]

    progress = st.progress(0)
    total = len(combos)
    completed = 0

    def process_combo(h1, h2):
        combo_results = []
        climb_time = abs(h2 - h1) * 0.3048 / climb_rate
        cruise_time = duration_sec - climb_time
        for frac in np.linspace(0.1, 0.9, 9):
            t1 = cruise_time * frac
            t2 = cruise_time * (1 - frac)
            p0 = np.array([0, 0])
            p1 = p0 + wind_vectors[h1] * t1
            p2 = p1 + wind_vectors[h2] * t2
            area = 0.5 * abs((p1[0] - p0[0]) * (p2[1] - p0[1]) - (p2[0] - p0[0]) * (p1[1] - p0[1])) / 1e6
            combo_results.append({
                'h1': h1,
                'h2': h2,
                'dir1': round(interp_dirs[h1], 1),
                'dir2': round(interp_dirs[h2], 1),
                'Speed_h1': round(interp_speeds[h1], 2),
                'Speed_h2': round(interp_speeds[h2], 2),
                'T1': f"{int(t1//60)}:{int(t1%60):02d}",
                'T2': f"{int(t2//60)}:{int(t2%60):02d}",
                'Climb': f"{int(climb_time//60)}:{int(climb_time%60):02d}",
                'Area_km2': round(area, 2),
                'p0': p0, 'p1': p1, 'p2': p2
            })
        return combo_results

    all_results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_combo, h1, h2): (h1, h2) for h1, h2 in combos}
        for future in concurrent.futures.as_completed(futures):
            all_results.extend(future.result())
            completed += 1
            progress.progress(min(1.0, completed / total))

    progress.empty()
    return sorted(all_results, key=lambda x: -x['Area_km2'])[:10]

def simulate_landrun(df, duration_sec, climb_rate):
    return simulate_landrun_fast_parallel(df, duration_sec, climb_rate)

if df is not None and not df.empty:
    st.success("✅ Winddaten bereit.")
    results = simulate_landrun(df, flight_time_min * 60, climb_rate)
    if results:
        st.subheader("🏆 Top 10 Höhenkombinationen")
        def format_row(r):
            return {
                'Höhe 1': f"{int(r['h1'])} ft",
                'Zeit 1': r['T1'],
                'Richtung 1': f"{r['dir1']}°",
                'Speed 1': f"{r['Speed_h1']:.2f}",
                'Höhe 2': f"{int(r['h2'])} ft",
                'Zeit 2': r['T2'],
                'Richtung 2': f"{r['dir2']}°",
                'Speed 2': f"{r['Speed_h2']:.2f}",
                'Climb': r['Climb'],
                'Fläche [km²]': f"{r['Area_km2']:.2f}"
            }
        table = pd.DataFrame([format_row(r) for r in results])
        styled = table.style.set_table_attributes('style="font-size: 13px; width: 100%;"') \
            .apply(lambda x: ['background-color: #f2f2f2' if x.name % 2 == 1 else '' for _ in x], axis=1) \
            .hide(axis="index")
        st.markdown(styled.to_html(), unsafe_allow_html=True)

        st.subheader("📍 Flugbahn der besten Variante")
        best = results[0]
        x, y = zip(best['p0'], best['p1'], best['p2'])
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.plot(x, y, marker='o', linestyle='-', color='blue')
        for i, (px, py) in enumerate(zip(x, y)):
            ax.text(px, py, f"P{i+1}", fontsize=12, ha='left', va='bottom')
        ax.arrow(x[0], y[0] + 400, 0, 100, head_width=50, head_length=50, fc='gray', ec='gray')
        ax.text(x[0], y[0] + 520, "N", ha='center', fontsize=12)
        ax.set_title("Flugbahn mit realistischen Übergängen")
        ax.set_xlabel("Ostverschiebung [m]")
        ax.set_ylabel("Nordverschiebung [m]")
        ax.set_aspect('equal')
        ax.grid(True)
        st.pyplot(fig)
