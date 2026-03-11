import streamlit as st
import pandas as pd
import requests
import time
import re
import json
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1mmPHzEY9p7ohdzvIYvwQOvqmKNa_8VQdZyl4sj1nksw/export?format=csv&gid=0"
# Remplacez par votre URL de script Google Apps Script
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxhetuY5QpJEvl-Wv1BMGej5FeW6S3-WDcbS1DwcwUVT-Yt3e8th1XG9pPCcbrwPu5ITw/exec"

SIMU_CONFIG = {
    "Passerelle 1": "#B3E5FC", 
    "Machine": "#C8E6C9",      
    "Radar": "#FFF9C4",        
    "Manœuvre": "#F8BBD0"      
}

# Génération des créneaux de 15 minutes (06h à 20h)
QUARTS_HEURES = []
for h in range(6, 21):
    for m in ["00", "15", "30", "45"]:
        QUARTS_HEURES.append(f"{h:02d}:{m}")

st.set_page_config(page_title="⚓ Planning Naval", layout="wide")

# --- STYLE CSS (Grille et Tableaux) ---
st.markdown("""
    <style>
    .slot-container { display: flex !important; flex-direction: row !important; gap: 2px !important; width: 100% !important; height: 100%; }
    .calendar-cell { 
        flex: 1 !important; padding: 2px !important; border-radius: 2px !important; 
        font-size: 11px !important; border: 1px solid rgba(0,0,0,0.1) !important; 
        color: #000 !important; text-align: center !important; font-weight: bold; 
        min-height: 25px; display: flex; align-items: center; justify-content: center;
    }
    .time-col { font-size: 12px; font-weight: bold; color: #003366; text-align: right; padding-right: 10px; border-right: 2px solid #003366; }
    .grid-line-hour { border-bottom: 2px solid #ccc; height: 28px; }
    .grid-line-min { border-bottom: 1px dashed #eee; height: 28px; }
    .day-header { text-align: center; background-color: #003366; color: white; padding: 8px; border-radius: 4px; font-weight: bold; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS ---
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

# --- NAVIGATION SIDEBAR ---
menu = st.sidebar.radio("MENU", ["📅 Planning Hebdo", "📊 Statistiques", "🔐 Administration"])

# --- 1. PLANNING HEBDO ---
if menu == "📅 Planning Hebdo":
    st.title("⚓ Planning des Simulateurs")
    
    c1, c2, _ = st.columns([1, 1, 4])
    with c1: annee_sel = st.selectbox("Année", [2025, 2026, 2027], index=1)
    with c2: 
        curr_w = datetime.now().isocalendar()[1]
        semaine_sel = st.selectbox("Semaine", range(1, 54), index=curr_w-1)

    # Calcul des jours de la semaine
    jan4 = datetime(annee_sel, 1, 4)
    monday = (jan4 - timedelta(days=jan4.weekday())) + timedelta(weeks=semaine_sel-1)
    week_days = [monday + timedelta(days=i) for i in range(5)]

    # Affichage des jours
    cols = st.columns([0.6] + [1]*5)
    for i, d in enumerate(week_days):
        cols[i+1].markdown(f"<div class='day-header'>{d.strftime('%A')}<br>{d.strftime('%d/%m')}</div>", unsafe_allow_html=True)

    # Construction de la grille
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
                        # On n'affiche le nom que sur le premier quart d'heure du créneau
                        nums = re.findall(r'(\d+)', str(r['Horaire']))
                        h_start = f"{int(nums[0]):02d}:{int(nums[1] if len(nums)>1 else 0):02d}"
                        label = f"{r['Equipage']}" if h_start == q else ""
                        html += f'<div class="calendar-cell" style="background-color: {color};" title="{r["Simu"]}">{label}</div>'
                    html += '</div>'
                    st.markdown(html, unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='{'grid-line-hour' if is_pile else 'grid-line-min'}'></div>", unsafe_allow_html=True)

# --- 2. STATISTIQUES ---
elif menu == "📊 Statistiques":
    st.title("📊 Statistiques d'Utilisation")
    if not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Utilisation par Simulateur")
            st.bar_chart(df['Simu'].value_counts())
        with col2:
            st.subheader("Top Équipages")
            st.bar_chart(df['Equipage'].value_counts().head(10))
        
        st.subheader("Liste complète des réservations")
        st.dataframe(df.drop(columns=['Date_DT']), use_container_width=True)
    else:
        st.warning("Aucune donnée disponible.")

# --- 3. ADMINISTRATION ---
elif menu == "🔐 Administration":
    st.title("⚙️ Administration du Planning")
    
    tab1, tab2 = st.tabs(["➕ Ajouter", "🗑️ Supprimer"])
    
    with tab1:
        with st.form("form_add"):
            d = st.date_input("Date")
            eq = st.text_input("Équipage / Nom")
            hr = st.text_input("Horaire (Format: 08h00 - 12h00)")
            sm = st.selectbox("Simulateur", list(SIMU_CONFIG.keys()))
            if st.form_submit_button("Ajouter à la base"):
                if d and eq and hr:
                    payload = {
                        "action": "add",
                        "date": d.strftime("%d/%m/%Y"),
                        "equipage": eq,
                        "horaire": hr,
                        "simu": sm
                    }
                    try:
                        requests.post(SCRIPT_URL, data=json.dumps(payload))
                        st.success(f"Réservation pour {eq} ajoutée !")
                        time.sleep(1)
                        st.rerun()
                    except:
                        st.error("Erreur de connexion au script.")
                else:
                    st.error("Veuillez remplir tous les champs.")

    with tab2:
        if not df.empty:
            st.write("Sélectionnez une ligne à supprimer :")
            # On trie pour faciliter la recherche
            df_sorted = df.sort_values(by=['Date_DT'], ascending=False)
            target_idx = st.selectbox("Réservation :", df_sorted.index, 
                                    format_func=lambda x: f"{df.loc[x, 'Date']} - {df.loc[x, 'Equipage']} ({df.loc[x, 'Simu']})")
            
            if st.button("❌ Supprimer définitivement"):
                # +2 car Google Sheet commence à 1 et a une ligne d'en-tête
                payload = {"action": "delete", "row": int(target_idx) + 2}
                try:
                    requests.post(SCRIPT_URL, data=json.dumps(payload))
                    st.warning("Ligne supprimée.")
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("Erreur lors de la suppression.")
        else:
            st.write("Rien à supprimer.")
