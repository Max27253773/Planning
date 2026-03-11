import streamlit as st
import pandas as pd
import requests
import time
import re
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1mmPHzEY9p7ohdzvIYvwQOvqmKNa_8VQdZyl4sj1nksw/export?format=csv&gid=0"

SIMU_CONFIG = {
    "Passerelle 1": "#B3E5FC", 
    "Machine": "#C8E6C9",      
    "Radar": "#FFF9C4",        
    "Manœuvre": "#F8BBD0"      
}

H_DEBUT = 6
H_FIN = 20
HAUTEUR_HEURE = 60 

st.set_page_config(page_title="Planning Naval", layout="wide")

# --- CSS GLOBAL ---
st.markdown(f"""
    <style>
    .day-column-container {{
        position: relative;
        width: 100%;
        height: {(H_FIN - H_DEBUT) * HAUTEUR_HEURE}px;
        background-color: white;
        border: 1px solid #ccc;
        background-image: linear-gradient(#f0f0f0 1px, transparent 1px);
        background-size: 100% {HAUTEUR_HEURE}px;
        margin-bottom: 20px;
    }}
    .resa-item {{
        position: absolute;
        left: 2px;
        right: 2px;
        border-radius: 4px;
        border: 2px solid rgba(0,0,0,0.3); /* Bordure plus forte pour test */
        padding: 4px;
        font-size: 11px;
        font-weight: bold;
        color: black !important;
        overflow: hidden;
        z-index: 999;
        display: flex;
        flex-direction: column;
        justify-content: center;
        text-align: center;
    }}
    .time-label-cell {{
        height: {HAUTEUR_HEURE}px;
        line-height: {HAUTEUR_HEURE}px;
        font-weight: bold;
        text-align: right;
        padding-right: 10px;
        color: #003366;
    }}
    .header-box {{
        text-align: center;
        background-color: #003366;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 5px;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

def parse_horaire_precis(h_str):
    if pd.isna(h_str): return None
    try:
        nums = re.findall(r'(\d+)', str(h_str))
        if len(nums) >= 4:
            h1, m1, h2, m2 = map(int, nums[:4])
            return [h1 + m1/60, h2 + m2/60]
        elif len(nums) == 2:
            return [float(nums[0]), float(nums[1])]
        return None
    except: return None

@st.cache_data(ttl=2)
def load_data():
    try:
        url = f"{SHEET_CSV_URL}&v={time.time()}"
        data = pd.read_csv(url)
        data['Date_DT'] = pd.to_datetime(data['Date'], dayfirst=True, errors='coerce')
        return data.dropna(subset=['Date_DT', 'Horaire'])
    except: return pd.DataFrame()

df = load_data()

# --- INTERFACE ---
st.title("⚓ Planning Naval Haute Précision")

c1, c2, _ = st.columns([1, 1, 4])
with c1: annee_sel = st.selectbox("Année", [2025, 2026, 2027], index=1)
with c2: 
    curr_w = datetime.now().isocalendar()[1]
    semaine_sel = st.selectbox("Semaine", range(1, 54), index=curr_w-1)

jan4 = datetime(annee_sel, 1, 4)
monday = (jan4 - timedelta(days=jan4.weekday())) + timedelta(weeks=semaine_sel-1)
week_days = [monday + timedelta(days=i) for i in range(5)]

cols = st.columns([0.6] + [1]*5)

# Colonne des heures
with cols[0]:
    st.markdown("<div style='margin-top:55px;'>", unsafe_allow_html=True)
    for h in range(H_DEBUT, H_FIN + 1):
        st.markdown(f"<div class='time-label-cell'>{h:02d}:00</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Colonnes des jours
for i, d in enumerate(week_days):
    with cols[i+1]:
        st.markdown(f"<div class='header-box'>{d.strftime('%A')}<br>{d.strftime('%d/%m')}</div>", unsafe_allow_html=True)
        
        # On prépare TOUT le HTML du jour dans une seule chaîne
        day_html = "<div class='day-column-container'>"
        
        day_resas = df[df['Date_DT'].dt.date == d.date()]
        
        for _, r in day_resas.iterrows():
            heures = parse_horaire_precis(r['Horaire'])
            if heures:
                h_start, h_end = heures[0], heures[1]
                if h_end > H_DEBUT and h_start < H_FIN:
                    top = (max(h_start, H_DEBUT) - H_DEBUT) * HAUTEUR_HEURE
                    height = (min(h_end, H_FIN) - max(h_start, H_DEBUT)) * HAUTEUR_HEURE
                    color = SIMU_CONFIG.get(str(r['Simu']).strip(), "#EEEEEE")
                    
                    day_html += f"""
                        <div class="resa-item" style="top: {top}px; height: {height}px; background-color: {color};">
                            {r['Equipage']}<br><span style='font-size:8px;'>{r['Simu']}</span>
                        </div>
                    """
        
        day_html += "</div>"
        # Affichage unique par colonne
        st.markdown(day_html, unsafe_allow_html=True)
