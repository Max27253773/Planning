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

# Couleurs des simulateurs
SIMU_CONFIG = {
    "Passerelle 1": "#B3E5FC", # Bleu
    "Machine": "#C8E6C9",      # Vert
    "Radar": "#FFF9C4",        # Jaune
    "Manœuvre": "#F8BBD0"      # Rose
}

# Définition des tranches horaires
TRANCHES = [
    ("06:00", "08:00"), ("08:00", "10:00"), ("10:00", "12:00"),
    ("12:00", "14:00"), ("14:00", "16:00"), ("16:00", "18:00"),
    ("18:00", "20:00")
]

st.set_page_config(page_title="Planning Naval", layout="wide", page_icon="⚓")

# --- STYLE CSS ---
st.markdown("""
    <style>
    .calendar-cell {
        padding: 6px;
        border-radius: 4px;
        margin-bottom: 4px;
        font-size: 11px;
        border: 1px solid rgba(0,0,0,0.1);
        color: #000 !important;
        font-weight: 500;
        text-align: center;
    }
    .time-label {
        background-color: #f1f3f4;
        font-weight: bold;
        text-align: center;
        padding: 15px 5px;
        border-radius: 5px;
        border: 1px solid #ddd;
        color: #333;
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

# --- FONCTIONS ---
def appartient_a_tranche(horaire_str, t_debut, t_fin):
    """Vérifie si une réservation commence dans une tranche donnée"""
    try:
        # Extrait l'heure de début (ex: "08h30" -> 8.5)
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

menu = st.sidebar.selectbox("Navigation ⚓", ["📅 Planning Hebdo", "📊 Résumé", "🔐 Admin"])

# --- 1. PLANNING VISUEL PAR HORAIRES ---
if menu == "📅 Planning Hebdo":
    st.title("🗓️ Planification Stratégique des Ressources")
    
    col_nav, _ = st.columns([2, 4])
    with col_nav:
        selected_date = st.date_input("Semaine du :", datetime.now())
    
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    week_days = [start_of_week + timedelta(days=i) for i in range(7)]
    day_names = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

    # En-têtes (Jours)
    cols = st.columns([1.2] + [1]*7)
    cols[0].write("") # Case vide en haut à gauche
    for i, d in enumerate(week_days):
        cols[i+1].markdown(f"<div class='day-header'>{day_names[i]}<br>{d.strftime('%d/%m')}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Lignes (Tranches Horaires)
    for t_start, t_end in TRANCHES:
        row_cols = st.columns([1.2] + [1]*7)
        # Colonne de gauche : l'heure
        row_cols[0].markdown(f"<div class='time-label'>{t_start} - {t_end}</div>", unsafe_allow_html=True)
        
        for i, d in enumerate(week_days):
            with row_cols[i+1]:
                # Filtrer les réservations pour ce jour et cette tranche
                mask = (df['Date_DT'].dt.date == d)
                resas_du_jour = df[mask]
                
                # Sous-filtrage par heure dans la tranche
                resas_tranche = resas_du_jour[resas_du_jour['Horaire'].apply(lambda x: appartient_a_tranche(x, t_start, t_end))]
                
                if not resas_tranche.empty:
                    for _, r in resas_tranche.iterrows():
                        color = SIMU_CONFIG.get(r['Simu'], "#EEEEEE")
                        st.markdown(f"""
                            <div class="calendar-cell" style="background-color: {color};">
                                <b>{r['Equipage']}</b><br>
                                {r['Simu']}<br>
                                <span style='font-size:10px;'>({r['Horaire']})</span>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown('<div style="min-height:60px; border: 0.5px dashed #ddd; margin-bottom:5px;"></div>', unsafe_allow_html=True)

# --- 2. ADMIN & STATS (RESTE DU CODE IDENTIQUE) ---
elif menu == "🔐 Admin":
    # Garder la même logique d'administration pour ajouter/modifier
    st.info("Utilisez l'onglet Admin pour ajouter des séances.")
