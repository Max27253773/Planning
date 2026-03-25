import streamlit as st
import pandas as pd
import time
import re
import json
from datetime import datetime, timedelta
from supabase import create_client

# --- 1. CONFIGURATION SUPABASE ---
# Ces clés permettent de connecter ton application à ta base de données
SUPABASE_URL = "https://uyqmviseejbvsngwbpkt.supabase.co"
SUPABASE_KEY = "sb_publishable_tEx11emOTmYUiXip8VeRTA_XsA8jfve"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="IO", layout="wide", initial_sidebar_state="expanded")

# --- 3. INITIALISATION DE LA SESSION ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False
if "role" not in st.session_state:
    st.session_state["role"] = None

# --- 4. LOGIQUE DE CONNEXION (DESIGN NÉOMORPHIQUE) ---
if not st.session_state["auth"]:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { visibility: hidden; transform: translateX(-100%); }
        header { visibility: hidden; }
        .main .block-container {
            padding-top: 8rem !important;
            max-width: 450px !important;
            margin: auto;
        }
        div[data-testid="stForm"] {
            border: 2px solid #000000 !important;
            border-radius: 15px !important;
            padding: 40px !important;
            background-color: #FDFDFD !important;
            box-shadow: 10px 10px 0px #000000 !important;
        }
        button[kind="primaryFormSubmit"] {
            background-color: #0026C7 !important;
            color: white !important;
            border: 2px solid #000000 !important;
            width: 100% !important;
            font-weight: bold !important;
            height: 3rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="background: linear-gradient(90deg, #0026C7 0%, #FFFFFF 50%, #C70000 100%); 
                    padding: 6px; border-radius: 6px; text-align: center; width: 45%; margin: 0 auto 30px auto; border: 2px solid black;">
            <p style="font-size: 20px; color: black; margin: 0; font-family: 'Impact'; letter-spacing: 3px;">⌬ IO</p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        st.markdown("<h2 style='text-align: center; color: black; margin-top: 0;'>CONNEXION</h2>", unsafe_allow_html=True)
        user_input = st.text_input("Identifiant")
        pw_input = st.text_input("Mot de passe", type="password")
        submit_auth = st.form_submit_button("SE CONNECTER")
        
        if submit_auth:
            credentials = {
                "UT": {"pw": "Azerty123*", "role": "Utilisateur"},
                "ANIM": {"pw": "Anim2026*", "role": "Animateur"}
            }
            if user_input in credentials and pw_input == credentials[user_input]["pw"]:
                st.session_state["auth"] = True
                st.session_state["role"] = credentials[user_input]["role"]
                st.rerun()
            else:
                st.error("Identifiants incorrects")
    st.stop()

# --- 5. STYLE CSS GLOBAL (UNE FOIS CONNECTÉ) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    header { visibility: visible !important; }
    [data-testid="stSidebar"] { 
        visibility: visible !important;
        background-color: #E2E8F0 !important; 
        border-right: 2px solid #000000 !important; 
    }
    .planning-frame {
        position: relative; width: 100%; background: #FFFFFF;
        height: 1260px; border: 1px solid #000; margin-bottom: 30px;
        overflow: hidden;
    }
    .hour-row-fixed {
        position: absolute; left: 0; right: 0; height: 45px;
        display: flex; align-items: center; border-bottom: 1px dashed #CCC;
    }
    .calendar-cell-unique { 
        position: absolute; z-index: 100; border: 2px solid #000000; 
        text-align: center; font-weight: 900; 
        display: flex; align-items: center; justify-content: center; 
        box-shadow: 2px 2px 0px rgba(0,0,0,1); box-sizing: border-box;
    }
    </style>
""", unsafe_allow_html=True)

# --- 6. BANDEAU D'ALERTE ---
st.markdown("""
    <div style="background-color: #FFFFFF; color: #FF0000; padding: 7px; border: 4px solid #FF0000; border-radius: 5px; text-align: center; font-weight: bold; font-size: 0.7rem; margin-bottom: 5px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);">
        ⚠️ ATTENTION : PASSEZ VOTRE TÉLÉPHONE EN "MODE CLAIR"<br>
        <span style="color: #000000; font-size: 0.7rem;">Le mode sombre rend certains textes invisibles</span>
    </div>
""", unsafe_allow_html=True)

# --- 7. CONFIGURATION LOCAUX & HORAIRES ---
LOCAL_CONFIG = {
    "JUP": "#1976D2", "MIN": "#C2185B", "JUN": "#757575",
    "BAC": "#388E3C", "MARS": "#D32F2F", "SAT": "#E65100",
    "CRO": "#A1887F", "NEK": "#C5A000", "PHO": "#DAA520",
    "PERS": "#558B2F", "SAG": "#4A148C"
}
QUARTS_HEURES = [f"{h:02d}:{m}" for h in range(6, 20) for m in ["00", "30"]] + ["20:00"]

# --- 8. FONCTIONS MOTEUR (SUPABASE) ---
@st.cache_data(ttl=2)
def load_data():
    try:
        response = supabase.table("planning").select("*").execute()
        data = pd.DataFrame(response.data)
        if not data.empty:
            data['Date_DT'] = pd.to_datetime(data['date'], errors='coerce')
            data = data.rename(columns={
                "equipe": "Equipe", "horaire": "Horaire", "local": "Local", 
                "responsable": "Responsable", "date": "Date"
            })
            return data
        return pd.DataFrame(columns=["id", "Date", "Equipe", "Horaire", "Local", "Responsable", "Date_DT"])
    except:
        return pd.DataFrame()

def db_add(date, equipe, horaire, local):
    payload = {"date": str(date), "equipe": equipe.upper(), "horaire": horaire, "local": local, "responsable": ""}
    supabase.table("planning").insert(payload).execute()
    st.cache_data.clear()

def db_update(row_id, date, equipe, horaire, local):
    payload = {"date": str(date), "equipe": equipe.upper(), "horaire": horaire, "local": local}
    supabase.table("planning").update(payload).eq("id", row_id).execute()
    st.cache_data.clear()

def db_delete(row_id):
    supabase.table("planning").delete().eq("id", row_id).execute()
    st.cache_data.clear()

def extraire_heures(horaire_str):
    try:
        nums = re.findall(r'(\d+)', str(horaire_str))
        if len(nums) >= 4:
            h_deb = int(nums) + int(nums)/60
            h_fin = int(nums) + int(nums)/60
            return h_deb, h_fin
    except: pass
    return None, None

def verifier_conflit(df, date_test, horaire_test, local_test, equipe_test, exclude_id=None):
    h_deb_new, h_fin_new = extraire_heures(horaire_test)
    if h_deb_new is None: return "block", "Format d'heure invalide."
    
    date_test_str = str(date_test)
    
    # 1. Conflit Local
    mask_local = (df['Date'] == date_test_str) & (df['Local'].str.upper() == local_test.upper())
    if exclude_id: mask_local = mask_local & (df['id'] != exclude_id)
    
    for _, row in df[mask_local].iterrows():
        h_deb_ex, h_fin_ex = extraire_heures(row['Horaire'])
        if h_deb_ex is not None and max(h_deb_new, h_deb_ex) < min(h_fin_new, h_fin_ex):
            return "block", f"ALERTE : Le local {local_test} est déjà pris."

    return "ok", ""

# --- 5. INTERFACE & SIDEBAR ---
LOCAL_CONFIG = {"JUP": "#1976D2", "MIN": "#C2185B", "JUN": "#757575", "BAC": "#388E3C", "MARS": "#D32F2F", "SAT": "#E65100", "CRO": "#A1887F", "NEK": "#C5A000", "PHO": "#DAA520", "PERS": "#558B2F", "SAG": "#4A148C"}
QUARTS_HEURES = [f"{h:02d}:{m}" for h in range(6, 20) for m in ["00", "30"]] + ["20:00"]

menus = ["📅 Planning", "🖥️ Supervision", "🔍 Rechercher", "📊 Statistiques"]
if st.session_state["role"] == "Animateur": menus += ["🎯 Assignation Responsables", "🔐 Administration"]

menu = st.sidebar.radio("MENU", menus)
st.sidebar.divider()
annee_sel = st.sidebar.selectbox("Année",, index=1) 
semaine_sel = st.sidebar.selectbox("Semaine", range(1, 54), index=datetime.now().isocalendar()-1)
local_sel = st.sidebar.selectbox("Local", list(LOCAL_CONFIG.keys()))
jours_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
choix_j = st.sidebar.selectbox("Jour", jours_fr, index=min(datetime.now().weekday(), 4))
mode_vue = st.sidebar.segmented_control("Format", ["Semaine", "Jour"], default="Jour")

# Calcul dates
monday = (datetime(annee_sel, 1, 4) - timedelta(days=datetime(annee_sel, 1, 4).weekday())) + timedelta(weeks=semaine_sel-1)
week_days = [monday + timedelta(days=i) for i in range(5)]
d_active = week_days[jours_fr.index(choix_j)]

# --- 6. LOGIQUE DES PAGES ---
df = load_data()
is_admin = (st.session_state["role"] == "Animateur")

# CSS dynamique
st.markdown(f"""<style>.calendar-cell-unique {{ position: absolute; z-index: 100; border: 2px solid #000; color: white; text-align: center; font-weight: 900; display: flex; align-items: center; justify-content: center; box-shadow: 2px 2px 0px black; } .planning-frame {{ position: relative; width: 100%; height: 1260px; border: 1px solid #000; overflow: hidden; }} .hour-row-fixed {{ position: absolute; left: 0; right: 0; height: 45px; display: flex; align-items: center; border-bottom: 1px dashed #CCC; }}</style>""", unsafe_allow_html=True)

if menu == "📅 Planning":
    st.title(f"📍 {local_sel}")
    c_color = LOCAL_CONFIG.get(local_sel, "#000")
    
    if mode_vue == "Jour":
        st.info(f"{choix_j} {d_active.strftime('%d/%m')}")
        html = '<div class="planning-frame">'
        for i, q in enumerate(QUARTS_HEURES[:29]):
            top = i * 45
            html += f'<div class="hour-row-fixed" style="top:{top}px;"><div style="width:60px; font-weight:900; color:black;">{q}</div></div>'
        
        resas = df[(df['Date'] == str(d_active.date())) & (df['Local'] == local_sel)]
        for _, r in resas.iterrows():
            h_d, h_f = extraire_heures(r['Horaire'])
            if h_d:
                top_p, haut = int((h_d-6)*90), int((h_f-h_d)*90)-2
                html += f'<div class="calendar-cell-unique" style="top:{top_p}px; height:{haut}px; left:65px; right:5px; background:{c_color};">{r["Equipe"]}</div>'
        st.markdown(html + "</div>", unsafe_allow_html=True)

elif menu == "🔐 Administration" and is_admin:
    st.title("⚙️ Gestion Supabase")
    tab1, tab2, tab3 = st.tabs(["➕ Ajouter", "📝 Modifier", "🗑️ Supprimer"])
    
    with tab1:
        with st.form("add"):
            d_a, e_a, h_a = st.date_input("Date"), st.text_input("Equipe"), st.text_input("Horaire (08:00-10:00)")
            if st.form_submit_button("VALIDER"):
                status, msg = verifier_conflit(df, d_a, h_a, local_sel, e_a)
                if status == "ok":
                    db_add(d_a, e_a, h_a, local_sel)
                    st.success("Ajouté !"); time.sleep(1); st.rerun()
                else: st.error(msg)

    with tab2:
        df_week = df[df['Date_DT'].dt.isocalendar().week == semaine_sel]
        if not df_week.empty:
            sel_id = st.selectbox("Ligne", df_week['id'].tolist(), format_func=lambda x: f"{df[df['id']==x]['Equipe'].values} - {df[df['id']==x]['Local'].values}")
            with st.form("edit"):
                row = df[df['id']==sel_id].iloc
                new_e, new_h = st.text_input("Equipe", row['Equipe']), st.text_input("Horaire", row['Horaire'])
                if st.form_submit_button("MODIFIER"):
                    db_update(sel_id, row['Date'], new_e, new_h, row['Local'])
                    st.success("Modifié !"); time.sleep(1); st.rerun()

    with tab3:
        id_del = st.selectbox("Supprimer", df['id'].tolist(), key="del")
        if st.button("SUPPRIMER DÉFINITIVEMENT", type="primary"):
            db_delete(id_del)
            st.success("Supprimé !"); time.sleep(1); st.rerun()

elif menu == "🎯 Assignation Responsables" and is_admin:
    st.title("🎯 Responsables")
    ANIMATEURS = ["MAX", "ALEKS", "ALEX", "MAEL", "ELIES", "LISE", "SIMON", "JOSS"]
    df_resp = df[df['Date_DT'].dt.isocalendar().week == semaine_sel].sort_values('Date')
    
    for _, row in df_resp.iterrows():
        with st.container():
            col1, col2 = st.columns()
            col1.write(f"**{row['Date']}** | {row['Horaire']} | {row['Equipe']} ({row['Local']})")
            current_idx = ANIMATEURS.index(row['Responsable']) if row['Responsable'] in ANIMATEURS else 0
            new_res = col2.selectbox("Resp", ANIMATEURS, index=current_idx, key=f"res_{row['id']}")
            if new_res != row['Responsable']:
                db_update_resp(row['id'], new_res)
                st.rerun()

elif menu == "🖥️ Supervision":
    st.title("🖥️ Vue d'ensemble")
    # (Affichage simplifié pour la supervision)
    st.dataframe(df[df['Date'] == str(d_active.date())][['Horaire', 'Local', 'Equipe', 'Responsable']], use_container_width=True)

elif menu == "🔍 Rechercher":
    st.title("🔍 Recherche")
    query = st.text_input("Nom de l'équipe").upper()
    if query:
        res = df[df['Equipe'].str.contains(query, na=False)]
        st.table(res[['Date', 'Horaire', 'Local', 'Responsable']])
        st.info("L'administration permet d'ajouter, modifier ou supprimer des créneaux de manière avancée.")
       
