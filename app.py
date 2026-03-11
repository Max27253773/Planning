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

# Définition des simulateurs et de leurs couleurs (Style Pastel comme ton image)
SIMU_CONFIG = {
    "Passerelle 1": "#B3E5FC", # Bleu clair
    "Machine": "#C8E6C9",      # Vert clair
    "Radar": "#FFF9C4",        # Jaune clair
    "Manœuvre": "#F8BBD0"      # Rose clair
}

st.set_page_config(page_title="Planning Naval 2026", layout="wide", page_icon="⚓")

# --- STYLE CSS POUR LA GRILLE ---
st.markdown("""
    <style>
    .calendar-cell {
        padding: 10px;
        border-radius: 5px;
        margin: 2px;
        font-size: 12px;
        min-height: 60px;
        border: 1px solid #ddd;
        color: #000 !important;
    }
    .day-header {
        text-align: center;
        background-color: #f0f2f6;
        padding: 10px;
        font-weight: bold;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CALCULS ---
def extraire_heures_precises(horaire_str):
    try:
        blocs = re.findall(r'(\d+)[h:]?(\d+)?', str(horaire_str))
        if len(blocs) >= 2:
            h1, m1 = int(blocs[0][0]), int(blocs[0][1]) if blocs[0][1] else 0
            h2, m2 = int(blocs[1][0]), int(blocs[1][1]) if blocs[1][1] else 0
            return round(abs(((h2*60)+m2) - ((h1*60)+m1)) / 60, 2)
        return 4.0
    except: return 4.0

@st.cache_data(ttl=2)
def load_data():
    try:
        url_force = f"{SHEET_CSV_URL}&v={time.time()}"
        data = pd.read_csv(url_force)
        data['Date_DT'] = pd.to_datetime(data['Date'], errors='coerce')
        data['Heures'] = data['Horaire'].apply(extraire_heures_precises)
        return data
    except: return pd.DataFrame(columns=["Date", "Equipage", "Horaire", "Simu"])

df = load_data()

# --- NAVIGATION ---
menu = st.sidebar.selectbox("Navigation ⚓", ["📅 Planning Visuel", "📊 Résumé d'Activité", "🔐 Admin"])

# --- 1. PLANNING VISUEL (STYLE CALENDRIER) ---
if menu == "📅 Planning Visuel":
    st.title("📅 Calendrier Hebdomadaire")

    # Sélection de la semaine
    col_nav1, col_nav2 = st.columns([1, 3])
    with col_nav1:
        date_ref = st.date_input("Semaine du :", datetime.now())
    
    # Calcul des jours de la semaine (Lundi au Dimanche)
    start_week = date_ref - timedelta(days=date_ref.weekday())
    days = [start_week + timedelta(days=i) for i in range(7)]
    days_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

    # Affichage des en-têtes de colonnes
    cols = st.columns([1.5] + [1]*7)
    cols[0].write("**Simulateurs**")
    for i, d in enumerate(days):
        cols[i+1].markdown(f"<div class='day-header'>{days_names[i]}<br>{d.strftime('%d/%m')}</div>", unsafe_allow_html=True)

    st.divider()

    # Affichage de la grille par simulateur
    for simu, color in SIMU_CONFIG.items():
        row_cols = st.columns([1.5] + [1]*7)
        row_cols[0].markdown(f"**{simu}**")
        
        for i, d in enumerate(days):
            # Filtrer les réservations pour ce simu et ce jour
            mask = (df['Simu'] == simu) & (df['Date_DT'].dt.date == d.date())
            resas = df[mask]
            
            with row_cols[i+1]:
                if not resas.empty:
                    for _, r in resas.iterrows():
                        st.markdown(f"""
                            <div class="calendar-cell" style="background-color: {color};">
                                <b>{r['Equipage']}</b><br>
                                {r['Horaire']}
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown('<div style="min-height:64px; border: 1px dashed #eee;"></div>', unsafe_allow_html=True)

# --- 2. RÉSUMÉ D'ACTIVITÉ ---
elif menu == "📊 Résumé d'Activité":
    st.header("📊 Synthèse")
    # (Le code précédent des statistiques s'insère ici)
    st.info("Sélectionnez l'onglet Planning pour voir le calendrier visuel.")

# --- 3. ADMINISTRATION ---
elif menu == "🔐 Admin":
    pwd = st.sidebar.text_input("Code", type="password")
    if pwd == "1234":
        t1, t2, t3 = st.tabs(["Ajouter", "Modifier", "Supprimer"])
        with t1:
            with st.form("add"):
                d = st.date_input("Date")
                e = st.text_input("Equipage")
                h = st.text_input("Horaire (ex: 08h30 - 12h00)")
                s = st.selectbox("Simu", list(SIMU_CONFIG.keys()))
                if st.form_submit_button("Valider"):
                    requests.post(SCRIPT_URL, data=json.dumps({"action":"add","date":str(d),"equipage":e,"horaire":h,"simu":s}))
                    st.cache_data.clear()
        # ... (Logique Modifier/Supprimer identique à avant)
