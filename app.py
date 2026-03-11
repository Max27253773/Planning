import streamlit as st
import pandas as pd
import requests
import time
import re
import json
from datetime import datetime, timedelta

# --- CONFIGURATION (VERROUILLÉE) ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1mmPHzEY9p7ohdzvIYvwQOvqmKNa_8VQdZyl4sj1nksw/export?format=csv&gid=0"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxhetuY5QpJEvl-Wv1BMGej5FeW6S3-WDcbS1DwcwUVT-Yt3e8th1XG9pPCcbrwPu5ITw/exec"
ADMIN_PASSWORD = "1234" 

SIMU_CONFIG = {
    "JUPITER": "#B3E5FC", "MINERVE": "#C8E6C9", "JUNON": "#FFF9C4",        
    "BACCHUS": "#F8BBD0", "MARS": "#E1BEE7", "SATURNE": "#FFCCBC",
    "CRONOS": "#D1C4E9", "NEKKAR": "#CFD8DC", "PHOBOS": "#F0F4C3",
    "PERSEE": "#B2DFDB", "SAGITTAIRE": "#FFE0B2"
}

# Plage horaire : de 06:00 à 20:00 inclus
QUARTS_HEURES = [f"{h:02d}:{m}" for h in range(6, 21) for m in ["00", "30"]]

st.set_page_config(page_title="⚓ Planning Naval", layout="wide")

# --- STYLE CSS ---
st.markdown("""
    <style>
    .slot-wrapper { position: relative; width: 100%; height: 45px; }
    .calendar-cell-unique { 
        position: absolute; top: 2px; left: 2px; right: 2px;
        z-index: 100; padding: 4px; border-radius: 4px; 
        font-size: 11px; border: 1px solid rgba(0,0,0,0.2); 
        color: #000 !important; text-align: center; font-weight: bold;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        overflow: hidden; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        pointer-events: none;
    }
    .time-col-full { font-size: 14px; font-weight: 900; color: #003366; text-align: right; padding-right: 15px; border-right: 4px solid #003366; }
    .time-col-half { font-size: 13px; font-style: italic; font-weight: 400; color: #555; text-align: right; padding-right: 15px; border-right: 4px solid #99abc0; }
    .grid-line-hour { border-bottom: 2px solid #888; height: 45px; background-color: rgba(0,0,0,0.02); }
    .grid-line-min { border-bottom: 1px dashed #ccc; height: 45px; }
    .day-header { text-align: center; background-color: #003366; color: white; padding: 10px; border-radius: 4px; font-weight: bold; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE ---
def extraire_heures(horaire_str):
    try:
        nums = re.findall(r'(\d+)', str(horaire_str))
        if len(nums) >= 4:
            h_deb = int(nums[0]) + int(nums[1])/60
            h_fin = int(nums[2]) + int(nums[3])/60
            return h_deb, h_fin
    except: pass
    return None, None

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
menu = st.sidebar.radio("MENU", ["📅 Planning Hebdomadaire", "📊 Statistiques", "🔐 Administration"])

if menu == "📅 Planning Hebdomadaire":
    st.title("⚓ Planning des Simulateurs")
    c1, c2, _ = st.columns([1, 1, 4])
    with c1: annee_sel = st.selectbox("Année", [2025, 2026, 2027], index=1)
    with c2: semaine_sel = st.selectbox("Semaine", range(1, 54), index=datetime.now().isocalendar()[1]-1)

    monday = (datetime(annee_sel, 1, 4) - timedelta(days=datetime(annee_sel, 1, 4).weekday())) + timedelta(weeks=semaine_sel-1)
    week_days = [monday + timedelta(days=i) for i in range(5)]

    cols = st.columns([0.6] + [1]*5)
    jours_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    for i, d in enumerate(week_days):
        cols[i+1].markdown(f"<div class='day-header'>{jours_fr[i]}<br>{d.strftime('%d/%m')}</div>", unsafe_allow_html=True)

    for q in QUARTS_HEURES:
        if q == "20:30": continue
        row_cols = st.columns([0.6] + [1]*5)
        is_pile = q.endswith(":00")
        h_actuelle = int(q.split(':')[0]) + int(q.split(':')[1])/60
        
        row_cols[0].markdown(f"<div class='{'time-col-full' if is_pile else 'time-col-half'}'>{q}</div>", unsafe_allow_html=True)
        
        for i, d in enumerate(week_days):
            with row_cols[i+1]:
                resas_jour = df[df['Date_DT'].dt.date == d.date()]
                html_blocs = ""
                for _, r in resas_jour.iterrows():
                    h_deb, h_fin = extraire_heures(r['Horaire'])
                    if h_deb == h_actuelle:
                        hauteur_px = int((h_fin - h_deb) * 2 * 45) - 4 
                        color = SIMU_CONFIG.get(str(r['Simu']).strip().upper(), "#EEEEEE")
                        html_blocs += f'<div class="calendar-cell-unique" style="background-color:{color}; height:{hauteur_px}px;">{r["Equipage"]}<br><span style="font-size:9px; font-weight:normal;">{r["Simu"]}</span></div>'
                
                grid_class = "grid-line-hour" if is_pile else "grid-line-min"
                st.markdown(f"<div class='slot-wrapper'><div class='{grid_class}'></div>{html_blocs}</div>", unsafe_allow_html=True)

elif menu == "📊 Statistiques":
    st.title("📊 Statistiques")
    if not df.empty:
        st.bar_chart(df['Simu'].value_counts())
        st.dataframe(df.drop(columns=['Date_DT']), use_container_width=True)

elif menu == "🔐 Administration":
    st.title("⚙️ Gestion")
    pwd = st.sidebar.text_input("Mot de passe", type="password")
    
    if pwd == ADMIN_PASSWORD:
        tab1, tab2, tab3 = st.tabs(["➕ Ajouter", "📝 Modifier", "🗑️ Supprimer"])
        def format_resa(idx):
            r = df.loc[idx]
            return f"{r['Date']} | {r['Horaire']} | {r['Simu']} | {r['Equipage']}"
        
        with tab1:
            with st.form("form_add", clear_on_submit=True):
                d = st.date_input("Date", format="DD/MM/YYYY")
                eq = st.text_input("Équipage")
                hr = st.text_input("Horaire (ex: 08:30 - 12:00)")
                sm = st.selectbox("Simulateur", list(SIMU_CONFIG.keys()))
                if st.form_submit_button("VALIDER L'AJOUT"):
                    requests.post(SCRIPT_URL, data=json.dumps({"action":"add","date":d.strftime("%d/%m/%Y"),"equipage":eq,"horaire":hr,"simu":sm}))
                    st.success("Ajouté !"); time.sleep(1); st.rerun()
        
        with tab2:
            if not df.empty:
                idx = st.selectbox("Choisir la réservation à modifier", df.index, format_func=format_resa)
                with st.form("form_edit"):
                    ed = st.date_input("Date", value=df.loc[idx,'Date_DT'], format="DD/MM/YYYY")
                    ee = st.text_input("Équipage", df.loc[idx,'Equipage'])
                    eh = st.text_input("Horaire", df.loc[idx,'Horaire'])
                    es = st.selectbox("Simulateur", list(SIMU_CONFIG.keys()), index=list(SIMU_CONFIG.keys()).index(str(df.loc[idx,'Simu']).strip()) if str(df.loc[idx,'Simu']).strip() in SIMU_CONFIG else 0)
                    if st.form_submit_button("METTRE À JOUR"):
                        requests.post(SCRIPT_URL, data=json.dumps({"action":"update","row":int(idx)+2,"date":ed.strftime("%d/%m/%Y"),"equipage":ee,"horaire":eh,"simu":es}))
                        st.success("Mis à jour !"); time.sleep(1); st.rerun()
        
        with tab3:
            if not df.empty:
                target = st.selectbox("Choisir la réservation à supprimer", df.index, format_func=format_resa)
                # LA SÉCURITÉ EST ICI
                confirmer = st.checkbox("Cochez cette case pour confirmer la suppression")
                if st.button("❌ Supprimer définitivement", disabled=not confirmer):
                    requests.post(SCRIPT_URL, data=json.dumps({"action":"delete","row":int(target)+2}))
                    st.success("Supprimé !"); time.sleep(1); st.rerun()
    else: 
        st.info("Entrez le mot de passe.")
