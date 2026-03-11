import streamlit as st
import pandas as pd
import requests
import time
import json
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

st.set_page_config(page_title="Planning Naval Précis", layout="wide", page_icon="⚓")

# --- STYLE CSS RÉVISÉ ---
st.markdown(f"""
    <style>
    .main-container {{
        position: relative;
        width: 100%;
        height: {(H_FIN - H_DEBUT) * HAUTEUR_HEURE}px;
        background-color: white;
        border: 1px solid #ddd;
        background-image: linear-gradient(#eee 1px, transparent 1px);
        background-size: 100% {HAUTEUR_HEURE}px;
    }}
    .time-label {{
        height: {HAUTEUR_HEURE}px;
        line-height: {HAUTEUR_HEURE}px;
        font-weight: bold;
        color: #003366;
        text-align: right;
        padding-right: 10px;
        font-size: 13px;
    }}
    .resa-block {{
        position: absolute;
        left: 2px !important;
        right: 2px !important;
        border-radius: 4px;
        border: 1px solid rgba(0,0,0,0.2);
        padding: 4px;
        font-size: 11px;
        font-weight: bold;
        color: #000 !important;
        z-index: 100; /* Force l'affichage au premier plan */
        overflow: hidden;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }}
    .day-header {{
        text-align: center;
        background-color: #003366;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 2px;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- FONCTION DE LECTURE ---
def parse_horaire_precis(h_str):
    if pd.isna(h_str): return None
    try:
        # Extrait tous les nombres pour gérer 08h30, 8:30, 08-12, etc.
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
        data['Date_DT'] = pd.to_datetime(data['Date'], errors='coerce', dayfirst=True)
        return data.dropna(subset=['Date_DT', 'Horaire'])
    except:
        return pd.DataFrame()

df = load_data()

# --- INTERFACE ---
st.title("⚓ Planning Naval Haute Précision")

c1, c2, _ = st.columns([1, 1, 4])
with c1: annee_sel = st.selectbox("Année", [2025, 2026, 2027], index=1)
with c2: 
    curr_w = datetime.now().isocalendar()[1]
    semaine_sel = st.selectbox("Semaine", range(1, 54), index=curr_w-1)

# Calcul des jours
jan4 = datetime(annee_sel, 1, 4)
monday = (jan4 - timedelta(days=jan4.weekday())) + timedelta(weeks=semaine_sel-1)
week_days = [monday + timedelta(days=i) for i in range(5)]

# Affichage des colonnes
cols = st.columns([0.6] + [1]*5)

# Colonne des heures
with cols[0]:
    st.markdown("<div style='margin-top:42px;'>", unsafe_allow_html=True)
    for h in range(H_DEBUT, H_FIN + 1):
        st.markdown(f"<div class='time-label'>{h:02d}:00</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Colonnes des jours
for i, d in enumerate(week_days):
    with cols[i+1]:
        st.markdown(f"<div class='day-header'>{d.strftime('%A')}<br>{d.strftime('%d/%m')}</div>", unsafe_allow_html=True)
        
        # Le conteneur blanc de la journée
        st.markdown("<div class='main-container'>", unsafe_allow_html=True)
        
        day_resas = df[df['Date_DT'].dt.date == d.date()]
        
        for _, r in day_resas.iterrows():
            heures = parse_horaire_precis(r['Horaire'])
            if heures:
                h_start, h_end = heures[0], heures[1]
                
                if h_end > H_DEBUT and h_start < H_FIN:
                    # Calcul de la position
                    top = (max(h_start, H_DEBUT) - H_DEBUT) * HAUTEUR_HEURE
                    height = (min(h_end, H_FIN) - max(h_start, H_DEBUT)) * HAUTEUR_HEURE
                    
                    color = SIMU_CONFIG.get(r['Simu'], "#EEEEEE")
                    
                    # On injecte le bloc
                    st.markdown(f"""
                        <div class="resa-block" style="top: {top}px; height: {height}px; background-color: {color};">
                            <div style="line-height:1.1;">{r['Equipage']}</div>
                            <div style="font-size:9px; font-weight:normal; opacity:0.8;">{r['Simu']}</div>
                        </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
