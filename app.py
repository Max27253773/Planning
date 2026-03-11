import streamlit as st
import pandas as pd
import requests
import time
import json
import re
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1mmPHzEY9p7ohdzvIYvwQOvqmKNa_8VQdZyl4sj1nksw/export?format=csv&gid=0"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxhetuY5QpJEvl-Wv1BMGej5FeW6S3-WDcbS1DwcwUVT-Yt3e8th1XG9pPCcbrwPu5ITw/exec"

SIMU_CONFIG = {
    "Passerelle 1": "#B3E5FC", 
    "Machine": "#C8E6C9",      
    "Radar": "#FFF9C4",        
    "Manœuvre": "#F8BBD0"      
}

TRANCHES = [
    ("06:00", "08:00"), ("08:00", "10:00"), ("10:00", "12:00"),
    ("12:00", "14:00"), ("14:00", "16:00"), ("16:00", "18:00"),
    ("18:00", "20:00")
]

st.set_page_config(page_title="Planning Naval", layout="wide", page_icon="⚓")

# --- STYLE CSS (FLUIDE & CÔTE À CÔTE) ---
st.markdown("""
    <style>
    .slot-container {
        display: flex;
        flex-direction: row;
        gap: 5px;
        width: 100%;
    }
    .calendar-cell {
        flex: 1;
        padding: 8px 4px;
        border-radius: 4px;
        font-size: 11px;
        border: 1px solid rgba(0,0,0,0.1);
        color: #000 !important;
        text-align: center;
        min-width: 0; /* Évite le débordement */
        word-wrap: break-word;
    }
    .time-label {
        background-color: #f8f9fa;
        font-weight: bold;
        text-align: center;
        color: #003366;
        border-right: 2px solid #003366;
        padding: 10px 0;
    }
    .day-header {
        text-align: center;
        background-color: #003366;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTION DE FILTRAGE ---
def appartient_a_tranche(horaire_str, t_debut, t_fin):
    try:
        match = re.search(r'(\d+)[h:]?(\d+)?', str(horaire_str))
        if match:
            h = int(match.group(1))
            m = int(match.group(2)) if match.group(2) else 0
            heure_resa = h + (m/60)
            h_start = int(t_debut.split(':')[0])
            h_end = int(t_fin.split(':')[0])
            return h_start <= heure_resa < h_end
        return False
    except: return False

@st.cache_data(ttl=2)
def load_data():
    try:
        url_force = f"{SHEET_CSV_URL}&v={time.time()}"
        data = pd.read_csv(url_force)
        data['Date_DT'] = pd.to_datetime(data['Date'], errors='coerce')
        return data.dropna(subset=['Date_DT'])
    except:
        return pd.DataFrame(columns=["Date", "Equipage", "Horaire", "Simu", "Date_DT"])

df = load_data()

menu = st.sidebar.selectbox("Navigation ⚓", ["📅 Planning Semaine", "📊 Résumé", "🔐 Admin"])

if menu == "📅 Planning Semaine":
    st.title("🗓️ Planning Hebdomadaire des Simulateurs")
    
    col_nav, _ = st.columns([2, 4])
    with col_nav:
        selected_date = st.date_input("Semaine du :", datetime.now())
    
    # Lundi de la semaine sélectionnée
    start_of_week = (selected_date - timedelta(days=selected_date.weekday()))
    # On crée une liste d'objets DATE (pas datetime)
    week_days = [(start_of_week + timedelta(days=i)) for i in range(5)]
    day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]

    # En-têtes
    cols = st.columns([0.7] + [1]*5)
    for i, d in enumerate(week_days):
        cols[i+1].markdown(f"<div class='day-header'>{day_names[i]}<br>{d.strftime('%d/%m')}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Grille horaire
    for t_start, t_end in TRANCHES:
        row_cols = st.columns([0.7] + [1]*5)
        row_cols[0].markdown(f"<div class='time-label'>{t_start}<br>{t_end}</div>", unsafe_allow_html=True)
        
        for i, d in enumerate(week_days):
            with row_cols[i+1]:
                # CORRECTION ICI : d est déjà une date, on compare directement
                mask = (df['Date_DT'].dt.date == d)
                resas_du_jour = df[mask]
                resas_tranche = resas_du_jour[resas_du_jour['Horaire'].apply(lambda x: appartient_a_tranche(x, t_start, t_end))]
                
                if not resas_tranche.empty:
                    html_content = '<div class="slot-container">'
                    for _, r in resas_tranche.iterrows():
                        color = SIMU_CONFIG.get(r['Simu'], "#EEEEEE")
                        html_content += f"""
                            <div class="calendar-cell" style="background-color: {color};">
                                <b>{r['Equipage']}</b><br>{r['Simu']}
                            </div>
                        """
                    html_content += '</div>'
                    st.markdown(html_content, unsafe_allow_html=True)
                else:
                    st.markdown('<div style="min-height:50px; border-bottom: 1px solid #f0f2f6;"></div>', unsafe_allow_html=True)
        st.divider()

# --- BLOCS ADMIN (IDENTIQUES AU CODE PRÉCÉDENT) ---
elif menu == "🔐 Admin":
    st.subheader("Gestion des séances")
    # ... (Ajouter / Modifier / Supprimer)
