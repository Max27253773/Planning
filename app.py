import streamlit as st
import pandas as pd
import requests
import time
import re
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1mmPHzEY9p7ohdzvIYvwQOvqmKNa_8VQdZyl4sj1nksw/export?format=csv&gid=0"
# Remplacez par votre URL de script Google Apps Script pour l'admin
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxhetuY5QpJEvl-Wv1BMGej5FeW6S3-WDcbS1DwcwUVT-Yt3e8th1XG9pPCcbrwPu5ITw/exec"

SIMU_CONFIG = {
    "Passerelle 1": "#B3E5FC", 
    "Machine": "#C8E6C9",      
    "Radar": "#FFF9C4",        
    "Manœuvre": "#F8BBD0"      
}

QUARTS_HEURES = []
for h in range(6, 21):
    for m in ["00", "15", "30", "45"]:
        QUARTS_HEURES.append(f"{h:02d}:{m}")

st.set_page_config(page_title="Naval Planning Pro", layout="wide", page_icon="⚓")

# --- STYLE CSS ---
st.markdown("""
    <style>
    .slot-container { display: flex !important; flex-direction: row !important; gap: 2px !important; width: 100% !important; height: 100%; }
    .calendar-cell { flex: 1 !important; padding: 2px !important; border-radius: 2px !important; font-size: 10px !important; border: 1px solid rgba(0,0,0,0.1) !important; color: #000 !important; text-align: center !important; font-weight: bold; min-height: 22px; display: flex; align-items: center; justify-content: center; }
    .time-col { font-size: 12px; font-weight: bold; color: #003366; text-align: right; padding-right: 10px; border-right: 2px solid #003366; }
    .grid-line-hour { border-bottom: 2px solid #ccc; height: 26px; }
    .grid-line-min { border-bottom: 1px dashed #eee; height: 26px; }
    .day-header { text-align: center; background-color: #003366; color: white; padding: 8px; border-radius: 4px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS LOGIQUES ---
def est_dans_quart_heure(horaire_str, quart_str):
    try:
        nums = re.findall(r'(\d+)', str(horaire_str))
        if len(nums) >= 4:
            debut = int(nums[0]) + int(nums[1])/60
            fin = int(nums[2]) + int(nums[3])/60
        elif len(nums) == 2:
            debut, fin = float(nums[0]), float(nums[1])
        else: return False
        h_q, m_q = map(int, quart_str.split(':'))
        temps_q = h_q + m_q/60
        return debut <= temps_q < fin
    except: return False

@st.cache_data(ttl=2)
def load_data():
    try:
        url = f"{SHEET_CSV_URL}&v={time.time()}"
        data = pd.read_csv(url)
        data['Date_DT'] = pd.to_datetime(data['Date'], dayfirst=True, errors='coerce')
        return data.dropna(subset=['Date_DT', 'Horaire'])
    except: return pd.DataFrame()

df = load_data()

# --- NAVIGATION ---
menu = st.sidebar.selectbox("Navigation ⚓", ["📅 Planning Hebdo", "📊 Statistiques", "🔐 Administration"])

if menu == "📅 Planning Hebdo":
    st.title("🗓️ Planning de Navigation")
    
    c1, c2, _ = st.columns([1, 1, 4])
    with c1: annee_sel = st.selectbox("Année", [2025, 2026, 2027], index=1)
    with c2: 
        curr_w = datetime.now().isocalendar()[1]
        semaine_sel = st.selectbox("Semaine", range(1, 54), index=curr_w-1)

    jan4 = datetime(annee_sel, 1, 4)
    monday = (jan4 - timedelta(days=jan4.weekday())) + timedelta(weeks=semaine_sel-1)
    week_days = [monday + timedelta(days=i) for i in range(5)]

    cols = st.columns([0.6] + [1]*5)
    for i, d in enumerate(week_days):
        cols[i+1].markdown(f"<div class='day-header'>{d.strftime('%A')}<br>{d.strftime('%d/%m')}</div>", unsafe_allow_html=True)

    for q in QUARTS_HEURES:
        row_cols = st.columns([0.6] + [1]*5)
        is_pile = q.endswith(":00")
        row_cols[0].markdown(f"<div class='time-col'>{q if is_pile else ''}</div>", unsafe_allow_html=True)
        
        for i, d in enumerate(week_days):
            with row_cols[i+1]:
                day_resas = df[df['Date_DT'].dt.date == d.date()]
                resas_actives = day_resas[day_resas['Horaire'].apply(lambda x: est_dans_quart_heure(x, q))]
                
                if not resas_actives.empty:
                    html = '<div class="slot-container">'
                    for _, r in resas_actives.iterrows():
                        color = SIMU_CONFIG.get(str(r['Simu']).strip(), "#EEEEEE")
                        nums = re.findall(r'(\d+)', str(r['Horaire']))
                        label = f"{r['Equipage']}" if nums and f"{int(nums[0]):02d}:{int(nums[1] if len(nums)>1 else 0):02d}" == q else ""
                        html += f'<div class="calendar-cell" style="background-color: {color};">{label}</div>'
                    html += '</div>'
                    st.markdown(html, unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='{'grid-line-hour' if is_pile else 'grid-line-min'}'></div>", unsafe_allow_html=True)

elif menu == "📊 Statistiques":
    st.title("📊 Analyse de l'Utilisation")
    if not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            st
