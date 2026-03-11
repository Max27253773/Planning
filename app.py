import streamlit as st
import pandas as pd
import requests
import time
import re
import json
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1mmPHzEY9p7ohdzvIYvwQOvqmKNa_8VQdZyl4sj1nksw/export?format=csv&gid=0"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxhetuY5QpJEvl-Wv1BMGej5FeW6S3-WDcbS1DwcwUVT-Yt3e8th1XG9pPCcbrwPu5ITw/exec"
ADMIN_PASSWORD = "1234" 

SIMU_CONFIG = {
    "JUPITER": "#B3E5FC", "MINERVE": "#C8E6C9", "JUNON": "#FFF9C4",        
    "BACCHUS": "#F8BBD0", "MARS": "#E1BEE7", "SATURNE": "#FFCCBC",
    "CRONOS": "#D1C4E9", "NEKKAR": "#CFD8DC", "PHOBOS": "#F0F4C3",
    "PERSEE": "#B2DFDB", "SAGITTAIRE": "#FFE0B2"
}

QUARTS_HEURES = [f"{h:02d}:{m}" for h in range(6, 21) for m in ["00", "30"]]

st.set_page_config(page_title="⚓ Planning Naval", layout="wide")

# --- STYLE CSS (Alignement Horizontal Parfait) ---
st.markdown("""
    <style>
    .slot-container { display: flex !important; flex-direction: row !important; gap: 2px !important; width: 100% !important; height: 100%; align-items: center; }
    
    .calendar-cell { 
        flex: 1 !important; padding: 4px !important; border-radius: 3px !important; 
        font-size: 12px !important; border: 1px solid rgba(0,0,0,0.1) !important; 
        color: #000 !important; text-align: center !important; font-weight: bold; 
        min-height: 35px; display: flex; align-items: center; justify-content: center;
        z-index: 2;
    }
    
    /* Conteneur de ligne pour aligner l'heure et la grille */
    .row-wrapper { display: flex; align-items: center; height: 45px; position: relative; }

    /* Style des textes horaires */
    .txt-base { width: 60px; text-align: right; padding-right: 15px; }
    .txt-plein { font-size: 14px !important; font-weight: 900 !important; color: #003366 !important; }
    .txt-demi { font-size: 13px !important; font-style: italic !important; font-weight: 400 !important; color: #777 !important; }

    /* Les lignes en face des horaires */
    .line-container { flex-grow: 1; height: 100%; display: flex; align-items: center; position: relative; }
    
    .line-style { width: 100%; position: absolute; top: 50%; z-index: 1; }
    .line-plein { border-top: 2px solid #333 !important; }
    .line-demi { border-top: 1.5px dashed #bbb !important; }
    
    .day-header { text-align: center; background-color: #003366; color: white; padding: 10px; border-radius: 4px; font-weight: bold; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE CHARGEMENT ---
@st.cache_data(ttl=2)
def load_data():
    try:
        url = f"{SHEET_CSV_URL}&v={time.time()}"
        data = pd.read_csv(url)
        data['Date_DT'] = pd.to_datetime(data['Date'], dayfirst=True, errors='coerce')
        return data.dropna(subset=['Date_DT', 'Horaire'])
    except: return pd.DataFrame()

def est_dans_quart_heure(horaire_str, quart_str):
    try:
        nums = re.findall(r'(\d+)', str(horaire_str))
        if len(nums) >= 4:
            debut, fin = int(nums[0]) + int(nums[1])/60, int(nums[2]) + int(nums[3])/60
        elif len(nums) == 2:
            debut, fin = float(nums[0]), float(nums[1])
        else: return False
        h_q, m_q = map(int, quart_str.split(':'))
        return debut <= (h_q + m_q/60) < fin
    except: return False

df = load_data()

# --- INTERFACE ---
menu = st.sidebar.radio("MENU", ["📅 Planning Hebdomadaire", "📊 Statistiques", "🔐 Administration"])

if menu == "📅 Planning Hebdomadaire":
    st.title("⚓ Planning des Simulateurs")
    c1, c2, _ = st.columns([1, 1, 4])
    with c1: annee_sel = st.selectbox("Année", [2025, 2026, 2027], index=1)
    with c2: semaine_sel = st.selectbox("Semaine", range(1, 54), index=datetime.now().isocalendar()[1]-1)

    monday = (datetime(annee_sel, 1, 4) - timedelta(days=datetime(annee_sel, 1, 4).weekday())) + timedelta(weeks=semaine_sel-1)
    week_days = [monday + timedelta(days=i) for i in range(5)]

    # En-têtes des jours
    cols = st.columns([0.7] + [1]*5)
    jours_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    for i, d in enumerate(week_days):
        cols[i+1].markdown(f"<div class='day-header'>{jours_fr[i]}<br>{d.strftime('%d/%m')}</div>", unsafe_allow_html=True)

    # Grille du planning
    for q in QUARTS_HEURES:
        row_cols = st.columns([0.7] + [1]*5)
        is_pile = q.endswith(":00")
        
        # Colonne Heure
        t_class = "txt-plein" if is_pile else "txt-demi"
        row_cols[0].markdown(f"<div class='txt-base {t_class}'>{q}</div>", unsafe_allow_html=True)
        
        # Colonnes Jours
        for i, d in enumerate(week_days):
            with row_cols[i+1]:
                resas = df[(df['Date_DT'].dt.date == d.date()) & (df['Horaire'].apply(lambda x: est_dans_quart_heure(x, q)))]
                
                l_class = "line-plein" if is_pile else "line-demi"
                
                # On superpose la ligne et le contenu
                html = f"<div class='line-container'><div class='line-style {l_class}'></div>"
                
                if not resas.empty:
                    html += '<div class="slot-container" style="position:relative; z-index:10;">'
                    for _, r in resas.iterrows():
                        color = SIMU_CONFIG.get(str(r['Simu']).strip(), "#EEEEEE")
                        html += f'<div class="calendar-cell" style="background-color: {color};">{r["Equipage"]}</div>'
                    html += '</div>'
                
                st.markdown(html + "</div>", unsafe_allow_html=True)

# --- STATS ET ADMIN (Restent identiques pour la stabilité) ---
elif menu == "📊 Statistiques":
    st.title("📊 Statistiques")
    if not df.empty:
        st.bar_chart(df['Simu'].value_counts())
        st.dataframe(df.drop(columns=['Date_DT']), use_container_width=True)

elif menu == "🔐 Administration":
    st.title("⚙️ Administration")
    pwd = st.sidebar.text_input("Mot de passe", type="password")
    if pwd == ADMIN_PASSWORD:
        tab1, tab2, tab3 = st.tabs(["➕ Ajouter", "📝 Modifier", "🗑️ Supprimer"])
        with tab1:
            with st.form("add"):
                d = st.date_input("Date", format="DD/MM/YYYY")
                eq = st.text_input("Équipage")
                hr = st.text_input("Horaire")
                sm = st.selectbox("Simu", list(SIMU_CONFIG.keys()))
                if st.form_submit_button("Ajouter"):
                    requests.post(SCRIPT_URL, data=json.dumps({"action":"add","date":d.strftime("%d/%m/%Y"),"equipage":eq,"horaire":hr,"simu":sm}))
                    st.rerun()
    else: st.info("Entrez le mot de passe.")
