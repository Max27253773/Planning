import streamlit as st
import pandas as pd
import time
import re
from datetime import datetime, timedelta
from supabase import create_client
from streamlit_option_menu import option_menu

# --- 1. CONFIGURATION & CONNEXION SUPABASE ---
# Remplace par tes vraies clés si celles-ci sont des exemples
SUPABASE_URL = "https://uyqmviseejbvsngwbpkt.supabase.co"
SUPABASE_KEY = "sb_publishable_tEx11emOTmYUiXip8VeRTA_XsA8jfve"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="IO Planning", layout="wide", initial_sidebar_state="expanded")

# --- 3. FONCTIONS MOTEUR (CORRIGÉES AVEC "Planning") ---

@st.cache_data(ttl=2)
def load_data():
    try:
        response = supabase.table("Planning").select("*").execute()
        data = pd.DataFrame(response.data)
        if not data.empty:
            # On harmonise le nom de la colonne date venant de Supabase
            if 'date' in data.columns:
                data = data.rename(columns={'date': 'Date_DT'})
            elif 'date_dt' in data.columns:
                data = data.rename(columns={'date_dt': 'Date_DT'})
                
            data['Date_DT'] = pd.to_datetime(data['Date_DT'], errors='coerce')
            
            # Harmonisation des autres colonnes pour correspondre au reste du code
            cols_map = {
                "equipe": "Equipe", "horaire": "Horaire", 
                "local": "Local", "responsable": "Responsable"
            }
            # On ne renomme que si la colonne en minuscule existe
            for old_col, new_col in cols_map.items():
                if old_col in data.columns:
                    data = data.rename(columns={old_col: new_col})
            return data
        return pd.DataFrame(columns=["id", "Date_DT", "Equipe", "Horaire", "Local", "Responsable"])
    except Exception as e:
        st.error(f"Erreur de chargement : {e}")
        return pd.DataFrame()

def db_add(date, equipe, horaire, local):
    payload = {"date": str(date), "equipe": equipe.upper(), "horaire": horaire, "local": local, "responsable": ""}
    # Changement ici : "Planning"
    supabase.table("Planning").insert(payload).execute()
    st.cache_data.clear()

def db_update(row_id, date, equipe, horaire, local):
    payload = {"date": str(date), "equipe": equipe.upper(), "horaire": horaire, "local": local}
    # Changement ici : "Planning"
    supabase.table("Planning").update(payload).eq("id", row_id).execute()
    st.cache_data.clear()

def db_delete(row_id):
    # Changement ici : "Planning"
    supabase.table("Planning").delete().eq("id", row_id).execute()
    st.cache_data.clear()

def db_update_resp(row_id, nom_resp):
    # Changement ici : "Planning"
    supabase.table("Planning").update({"responsable": nom_resp}).eq("id", row_id).execute()
    st.cache_data.clear()

def extraire_heures(horaire_str):
    try:
        nums = re.findall(r'(\d+)', str(horaire_str))
        if len(nums) >= 4:
            # Format attendu : 08:00 - 10:00 ou 08h00 10h00
            h1, m1, h2, m2 = map(int, nums[:4])
            return h1 + m1/60, h2 + m2/60
    except: pass
    return None, None

def verifier_conflit(df, date_test, horaire_test, local_test, equipe_test, exclude_id=None):
    h_deb_new, h_fin_new = extraire_heures(horaire_test)
    if h_deb_new is None: 
        return "block", "Format d'heure invalide (ex: 08:00 - 10:00)."
    date_test_dt = pd.to_datetime(date_test).date()
    mask = (df['Date_DT'].dt.date == date_test_dt) & (df['Local'].str.upper() == local_test.upper())
    
    if exclude_id: 
        mask = mask & (df['id'] != exclude_id)
        
    for _, row in df[mask].iterrows():
        h_ex_d, h_ex_f = extraire_heures(row['Horaire']) # Vérifie que 'Horaire' a bien un H majuscule
        if h_ex_d is not None and max(h_deb_new, h_ex_d) < min(h_fin_new, h_ex_f):
            return "block", f"Le local {local_test} est déjà occupé sur ce créneau."
            
    return "ok", ""
    
# --- 3. INITIALISATION DU SESSION STATE ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False
if "role" not in st.session_state:
    st.session_state["role"] = None

# --- 4. LOGIQUE VISUELLE DE CONNEXION ---
if not st.session_state["auth"]:
    st.markdown("""
        <style>
        /* 1. Style de l'arrière-plan principal (Lumineux et Doux) */
        .stApp {
            background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%) !important;
        }

        /* 2. Cache la sidebar et le header */
        [data-testid="stSidebar"] { visibility: hidden; transform: translateX(-100%); }
        header { visibility: hidden; }
        
        /* 3. Centrage et Conteneur principal */
        .main .block-container {
            padding-top: 8rem !important;
            max-width: 420px !important;
            margin: auto;
        }

        /* 4. LE FORMULAIRE "GLASSMORPHISM" LUMINEUX (Correction) */
        div[data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.3) !important; /* Transparence blanche douce */
            backdrop-filter: blur(15px) !important; /* Effet de flou dépoli marqué */
            -webkit-backdrop-filter: blur(15px) !important;
            border-radius: 25px !important; /* Bords très arrondis */
            padding: 3rem !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important; /* Bordure blanche ultra-fine */
            box-shadow: 0 10px 30px rgba(0,0,0,0.05) !important; /* Ombre douce */
        }

        /* 5. Style des titres (Discret) */
        h3 {
            color: #333 !important;
            font-family: sans-serif !important;
            font-weight: 400 !important;
            letter-spacing: 1px !important;
            text-align: center;
        }

        /* 6. Style des champs de saisie (Clairs, Arrondis) */
        .stTextInput input {
            background-color: rgba(255, 255, 255, 0.6) !important;
            color: #333 !important;
            border: 1px solid rgba(0, 0, 0, 0.1) !important;
            border-radius: 12px !important;
            padding: 12px !important;
        }

        /* 7. LE BOUTON : Sobre, Épuré, Gris clair */
        button[kind="primaryFormSubmit"], button[data-testid="baseButton-secondaryFormSubmit"] {
            background-color: rgba(0, 0, 0, 0.05) !important;
            color: #333 !important;
            border: 1px solid rgba(0, 0, 0, 0.1) !important;
            border-radius: 15px !important;
            width: 100% !important;
            font-weight: 600 !important;
            font-family: sans-serif !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            height: 3.5rem !important;
            transition: all 0.3s;
        }

        button[kind="primaryFormSubmit"]:hover {
            background-color: rgba(0, 0, 0, 0.1) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Logo IO avec dégradé
    st.markdown("""
        <div style="text-align: center; width: 60%; margin: 0 auto 30px auto;">
            <p style="font-size: 32px; color: #333; margin: 0; font-family: sans-serif; font-weight: 300; letter-spacing: 6px;">⌬ IO</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        st.markdown("<h2 style='text-align: center; color: black; margin-top: 0; font-family: sans-serif; font-weight: 900;'>CONNEXION</h2>", unsafe_allow_html=True)
        
        user_input = st.text_input("IDENTIFIANT")
        pw_input = st.text_input("MOT DE PASSE", type="password", placeholder="••••••••")
        
        submit_auth = st.form_submit_button("SE CONNECTER")
        
        if submit_auth:
            # Identifiants
            credentials = {
                "UT": {"pw": "Azerty123*", "role": "Utilisateur"},
                "ANIM": {"pw": "Anim2026*", "role": "Animateur"}
            }
            
            if user_input in credentials and pw_input == credentials[user_input]["pw"]:
                st.session_state["auth"] = True
                st.session_state["role"] = credentials[user_input]["role"]
                st.success(f"Accès accordé : {st.session_state['role']}")
                time.sleep(0.6)
                st.rerun()
            else:
                st.error("Identifiants ou mot de passe incorrects.")
    
    st.stop()

# --- 5. CONFIGURATION VISUELLE ---

LOCAL_CONFIG = {
    "JUP": "#1976D2", "MIN": "#C2185B", "JUN": "#757575", "BAC": "#388E3C", 
    "MARS": "#D32F2F", "SAT": "#E65100", "CRO": "#A1887F", "NEK": "#C5A000", 
    "PHO": "#DAA520", "PERS": "#558B2F", "SAG": "#4A148C"
}
QUARTS_HEURES = [f"{h:02d}:{m}" for h in range(6, 21) for m in ["00", "30"]]

# --- BANDEAU D'ALERTE FORCE (VISIBLE EN MODE SOMBRE) ---
st.markdown("""
    <div style="
        background-color: #FFFFFF; 
        color: #FF0000; 
        padding: 7px; 
        border: 4px solid #FF0000; 
        border-radius: 5px; 
        text-align: center; 
        font-weight: bold; 
        font-size: 0.7rem; 
        margin-bottom: 5px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    ">
        ⚠️ ATTENTION : PASSEZ VOTRE TÉLÉPHONE EN "MODE CLAIR"<br>
        <span style="color: #000000; font-size: 0.7rem;">
            Le mode sombre rend certains textes et plannings invisibles
        </span>
    </div>
    """, unsafe_allow_html=True)

# --- 7. INTERFACE (DESIGN MODERNE) ---
df = load_data()
df['Date_DT'] = pd.to_datetime(df['Date_DT'], errors='coerce')

# --- 7.1. CONFIGURATION DU MENU ---
opts = ["Planning", "Supervision", "Rechercher", "Stats"]
icons = ["calendar3", "display", "search", "bar-chart"]
st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">', unsafe_allow_html=True)

# Ajout des options Animateur
if st.session_state.get("role") == "Animateur":
    opts += ["Assignation", "Administration"]
    icons += ["person-check", "gear"]

# --- 7.2. AFFICHAGE DE LA SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #444; letter-spacing: 2px;'>⌬ IO</h2>", unsafe_allow_html=True)
    
    # Le menu stylisé (Remplace st.sidebar.radio)
    selected_nav = option_menu(
        menu_title=None,
        options=opts,
        icons=icons,
        default_index=0,
        styles={
            "container": {"padding": "5!important", "background-color": "transparent"},
            "icon": {"color": "#444", "font-size": "18px"}, 
            "nav-link": {
                "font-size": "15px", 
                "text-align": "left", 
                "margin": "5px", 
                "font-family": "sans-serif",
                "color": "#444"
            },
            "nav-link-selected": {
                "background-color": "white", 
                "color": "black", 
                "font-weight": "600",
                "box-shadow": "0px 4px 12px rgba(0,0,0,0.08)",
                "border-radius": "12px"
            },
        }
    )

    # Mapping pour la compatibilité avec le reste de ton code
    mapping = {
        "Planning": "📅 Planning", "Supervision": "🖥️ Supervision", 
        "Rechercher": "🔍 Rechercher", "Stats": "📊 Statistiques",
        "Assignation": "🎯 Assignation Responsables", "Administration": "🔐 Administration"
    }
    menu = mapping.get(selected_nav)

    # BLOC ACCÈS ADMIN STYLISÉ
    is_admin = False
    if st.session_state.get("role") == "Animateur":
        
        # Injection de style spécifique pour ce container (Bulle blanche, ombre douce, coins arrondis)
        st.markdown("""
            <style>
            .admin-container {
                background-color: white !important;
                border-radius: 12px !important;
                padding: 12px 15px !important;
                box-shadow: 0px 4px 12px rgba(0,0,0,0.08) !important;
                border: 1px solid #f0f0f0 !important;
                margin-top: 20px !important;
                margin-bottom: 10px !important;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .admin-icon {
                color: #444 !important;
                font-size: 18px !important; /* Même taille que les icônes du menu */
                margin-right: 12px !important; /* Espacement avec le texte */
                margin-top: -3px; /* Léger ajustement pour l'alignement vertical */
            }
            .admin-text {
                margin: 0 !important;
                color: #444 !important;
                font-size: 14px !important; /* Même taille que le texte du menu */
                font-weight: 600 !important;
                font-family: sans-serif !important;
                letter-spacing: 0.5px !important;
            }
            </style>
        """, unsafe_allow_html=True)

        # Le container stylisé "Bulle Blanche" avec l'icône Bootstrap Intégrée
        # 'bi-shield-lock' est l'icône correspondante (Bouclier + Cadenas)
        st.markdown("""
            <div class='admin-container'>
                <i class='bi-shield-lock admin-icon'></i>
                <p class='admin-text'>ACCÈS ADMIN</p>
            </div>
        """, unsafe_allow_html=True)
            
        # Champ de saisie minimaliste (sans label, avec placeholder)
        admin_key = st.text_input(
            "Clé d'accès", 
            type="password", 
            key="global_pwd", 
            label_visibility="collapsed", 
            placeholder="Entrez le mot de passe..."
        )
            
        # Feedback discret (au lieu des gros st.success/st.error)
        if admin_key == "1234":
            is_admin = True
            st.markdown("<p style='color: #28a745; font-size: 12px; text-align: center; font-weight: 500; margin-top: 5px;'>✓ Mode Admin Actif</p>", unsafe_allow_html=True)
        elif admin_key != "":
            st.markdown("<p style='color: #dc3545; font-size: 12px; text-align: center; font-weight: 500; margin-top: 5px;'>✗ Mot de passe incorrect</p>", unsafe_allow_html=True)
            
# --- CALCUL AUTOMATIQUE DATE/SEMAINE ---
maintenant = datetime.now()
annee_actuelle = maintenant.year
semaine_actuelle = maintenant.isocalendar()[1]
jour_actuel_idx = maintenant.weekday() 

annee_sel = st.sidebar.selectbox("Année", [2025, 2026, 2027], index=1)
semaine_sel = st.sidebar.selectbox("Semaine", range(1, 54), index=semaine_actuelle - 1)
jours_fr_liste = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
choix_j_global = st.sidebar.selectbox("Jour", jours_fr_liste, index=min(maintenant.weekday(), 4) if annee_sel == maintenant.year else 0)
local_sel = st.sidebar.selectbox("Local", list(LOCAL_CONFIG.keys()))

# --- OPTIONS D'AFFICHAGE ---
st.sidebar.markdown("<br>", unsafe_allow_html=True)

# Titre avec icône Bootstrap
st.sidebar.markdown("""
    <div style='display: flex; align-items: center; margin-left: 5px; margin-bottom: 8px;'>
        <i class="bi bi-phone" style="font-size: 16px; color: #444; margin-right: 10px;"></i>
        <span style="color: #444; font-size: 13px; font-weight: 600; font-family: sans-serif; letter-spacing: 0.5px;">
            OPTIONS D'AFFICHAGE
        </span>
    </div>
""", unsafe_allow_html=True)

mode_vue = st.sidebar.segmented_control(
    "vue_format", 
    ["Semaine", "Jour"], 
    default="Jour", 
    label_visibility="collapsed"
)

# --- COPYRIGHT ET SIGNATURE ---
st.sidebar.divider()
st.sidebar.markdown(
    """
    <div style='text-align: center; color: #666666; font-size: 0.8rem; padding: 10px;'>
        © 2026 <b>.........</b><br>
        Tous droits réservés<br>
        <span style='font-size: 0.7rem;'>Version Bêta - Planning </span>
    </div>
    """, 
    unsafe_allow_html=True
)

monday = (datetime(annee_sel, 1, 4) - timedelta(days=datetime(annee_sel, 1, 4).weekday())) + timedelta(weeks=semaine_sel-1)
week_days = [monday + timedelta(days=i) for i in range(5)]

d = week_days[jours_fr_liste.index(choix_j_global)]

current_color = LOCAL_CONFIG.get(local_sel, "#000000")
text_on_color = "#000000" if local_sel in ["PHOBOS", "NEKKAR"] else "#FFFFFF"

# --- CSS COMPLET ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #FFFFFF !important; }}
    [data-testid="stSidebar"] {{ background-color: #F0F0F0 !important; border-right: 2px solid #000000 !important; }}
    h1 {{ font-size: 1.8rem !important; font-weight: 900 !important; color: #000000 !important; }}
    
    /* Mode Jour : Cadre ajusté pour finir à 20h00 */
    .planning-frame {{
        position: relative; width: 100%; background: #FFFFFF;
        height: 1260px; /* Hauteur exacte pour 6h-20h (14h * 90px) */
        border: 1px solid #000; margin-bottom: 30px;
        overflow: hidden;
    }}
    .hour-row-fixed {{
        position: absolute; left: 0; right: 0; height: 45px;
        display: flex; align-items: center; border-bottom: 1px dashed #CCC; box-sizing: border-box;
    }}
    
    /* Mode Semaine : Grille flexible */
    .slot-container-week {{ position: relative; width: 100%; height: 45px; box-sizing: border-box; }}
    .grid-line-hour {{ border-bottom: 2px solid #333333 !important; height: 45px; box-sizing: border-box; }}
    .grid-line-min {{ border-bottom: 1px dashed #777777 !important; height: 45px; box-sizing: border-box; }}

    .calendar-cell-unique {{ 
        position: absolute; z-index: 100; border: 2px solid #000000; 
        color: {text_on_color} !important; text-align: center; font-weight: 900; 
        display: flex; align-items: center; justify-content: center; 
        box-shadow: 2px 2px 0px rgba(0,0,0,1); box-sizing: border-box;
    }}
    
    .stButton button {{ width: 100% !important; font-weight: bold !important; }}
    </style>
    """, unsafe_allow_html=True)

df_view = df[df['Local'].str.strip().str.upper() == local_sel.upper()]

df_view = df[df['Local'].str.strip().str.upper() == local_sel.upper()]

# --- FILTRAGE SÉCURISÉ ---
if not df.empty:
    df_view = df[df['Local'].str.strip().str.upper() == local_sel.upper()]
else:
    df_view = pd.DataFrame()

# --- NAVIGATION ---

if menu == "📅 Planning":
    st.markdown(f"<h1>{local_sel}</h1>", unsafe_allow_html=True)
    if mode_vue == "Jour":
        # On utilise choix_j_global qui vient de la sidebar
        d = week_days[jours_fr_liste.index(choix_j_global)]
        
        st.markdown(f"<div style='text-align:center; background-color:{current_color}; color:{text_on_color}; padding:8px; font-weight:900; border:2px solid black; box-shadow: 2px 2px 0px black; margin-bottom:10px;'>{choix_j_global} {d.strftime('%d/%m')}</div>", unsafe_allow_html=True)
        
        # --- DESSIN DU PLANNING ---
        html_jour = '<div class="planning-frame">'
        for i, q in enumerate(QUARTS_HEURES):
            if i >= 29: break
            top = i * 45
            style = "border-bottom: 2px solid #333;" if q.endswith(":00") else ""
            html_jour += f'<div class="hour-row-fixed" style="top:{top}px; {style}"><div style="width:60px; text-align:right; padding-right:8px; font-weight:900; border-right:3px solid {current_color}; background:#F0F2F6; height:100%; display:flex; align-items:center; justify-content:flex-end; color:black;">{q}</div></div>'
        
        resas = df_view[df_view['Date_DT'].dt.date == d.date()]
        for _, r in resas.iterrows():
            h_deb, h_f = extraire_heures(r['Horaire'])
            if h_deb is not None:
                top_p = int((h_deb - 6) * 90)
                haut = int((h_f - h_deb) * 90) - 2
                html_jour += f'<div class="calendar-cell-unique" style="top:{top_p}px; height:{haut}px; left:65px; right:5px; background-color:{current_color}; font-size:14px;">{r["Equipe"]}</div>'
        st.markdown(html_jour + '</div>', unsafe_allow_html=True)

        # --- QUICK BOOKING CONDITIONNEL ---
        if is_admin:
            with st.expander("⚡ RÉSERVATION RAPIDE", expanded=False):
               with st.form("quick_booking"):
                    c1, c2 = st.columns(2)
                    q_eq = c1.text_input("Équipe", placeholder="Nom")
                    q_hr = c2.text_input("Horaire", placeholder="08h00 - 10h00")
            
                    # Case à cocher pour forcer si doublon
                    force_confirm = st.checkbox("Autoriser le doublon (Equipe déjà ailleurs)")
            
                    if st.form_submit_button("Vérifier et valider"):
                        if q_eq and q_hr:
                            # On passe bien les 5 arguments à la fonction
                            status, msg = verifier_conflit(df, d, q_hr, local_sel, q_eq)
                    
                            if status == "block":
                                st.error(msg)
                            elif status == "warn" and not force_confirm:
                                st.warning(msg)
                                st.info("Cochez la case ci-dessus pour confirmer le doublon.")
                            else:
                                # Cas "ok" OU (cas "warn" ET case cochée)
                                requests.post(SCRIPT_URL, data=json.dumps({
                                    "action":"add", 
                                    "date":d.strftime("%d/%m/%Y"),
                                    "equipe":q_eq.upper(), 
                                    "horaire":q_hr, 
                                    "local":local_sel
                                }))
                                st.success("✅ Réservé !"), time.sleep(1), st.rerun()
                        else:
                            st.warning("Veuillez remplir les champs.")
    else:
        # MODE SEMAINE
        cols = st.columns([0.6] + [1]*5)
        for i, d in enumerate(week_days):
            cols[i+1].markdown(f"<div style='text-align:center; background-color:{current_color}; color:{text_on_color}; padding:8px; font-weight:900; border:2px solid black; box-shadow: 2px 2px 0px black;'>{jours_fr_liste[i]}<br>{d.strftime('%d/%m')}</div>", unsafe_allow_html=True)

        for q in QUARTS_HEURES:
            row_cols = st.columns([0.6] + [1]*5)
            is_pile = q.endswith(":00")
            h_act = int(q.split(':')[0]) + int(q.split(':')[1])/60
            border_style = f"border-right:4px solid {current_color};" if is_pile else "border-right:1px solid #CCC;"
            row_cols[0].markdown(f"<div style='height:45px; display:flex; align-items:center; justify-content:flex-end; padding-right:10px; font-weight:900; {border_style}'>{q}</div>", unsafe_allow_html=True)
            
            for i, d in enumerate(week_days):
                with row_cols[i+1]:
                    resas = df_view[df_view['Date_DT'].dt.date == d.date()]
                    html_bloc = ""
                    for _, r in resas.iterrows():
                        h_deb, h_fin = extraire_heures(r['Horaire'])
                        if h_deb == h_act:
                            hauteur_px = int((h_fin - h_deb) * 2 * 45) - 2
                            html_bloc += f'<div class="calendar-cell-unique" style="top:1px; left:2px; right:2px; height:{hauteur_px}px; background-color:{current_color}; font-size:10px;">{r["Equipe"]}</div>'
                    grid_class = 'grid-line-hour' if is_pile else 'grid-line-min'
                    st.markdown(f"<div class='slot-container-week'><div class='{grid_class}'></div>{html_bloc}</div>", unsafe_allow_html=True)

elif menu == "🖥️ Supervision":
    st.markdown("<h1>🖥️ Vue d'ensemble des locaux</h1>", unsafe_allow_html=True)
    
    # On utilise choix_j_global (sidebar) et d (calculé plus haut)
    st.info(f"Visualisation de tous les locaux pour le **{choix_j_global} {d.strftime('%d/%m/%Y')}**")

    # On utilise d pour le filtrage
    df_jour = df[df['Date_DT'].dt.date == d.date()]

    # Création de la grille de données (Heures en lignes, Locaux en colonnes)
    # On crée une liste d'heures (toutes les 30 min)
    heures_sup = [f"{h:02d}:{m}" for h in range(6, 20) for m in ["00", "30"]]
    
    # On prépare le tableau HTML
    html_sup = """
    <div style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 0.8rem;">
            <thead>
                <tr style="background-color: #f0f2f6;">
                    <th style="border: 1px solid #ddd; padding: 8px; position: sticky; left: 0; background: #f0f2f6; z-index: 10; color: black;">Heure</th>
    """
    
    # Ajout des colonnes pour chaque simulateur
    for s in LOCAL_CONFIG.keys():
        color = LOCAL_CONFIG[s]
        html_sup += f'<th style="border: 1px solid #ddd; padding: 8px; background-color: {color}; color: white; text-align: center; min-width: 80px;">{s}</th>'
    
    html_sup += "</tr></thead><tbody>"

    # Remplissage des lignes
    for h_str in heures_sup:
        h_val = int(h_str.split(':')[0]) + int(h_str.split(':')[1])/60
        html_sup += f'<tr><td style="border: 1px solid #ddd; padding: 4px; font-weight: bold; position: sticky; left: 0; background: white; z-index: 5; color: black;">{h_str}</td>'
        
        for s in LOCAL_CONFIG.keys():
            # Vérifier si une réservation existe pour ce local à cette heure
            occupe = False
            nom_eq = ""
            
            # On cherche les résas de ce local
            resas_local = df_jour[df_jour['Local'].str.strip().str.upper() == s.upper()]
            for _, r in resas_local.iterrows():
                h_deb, h_fin = extraire_heures(r['Horaire'])
                if h_deb is not None and h_deb <= h_val < h_fin:
                    occupe = True
                    nom_eq = r['Equipe']
                    break
            
            if occupe:
                color = LOCAL_CONFIG[s]
                html_sup += f'<td style="border: 1px solid #ddd; padding: 2px; background-color: {color}44; color: black; text-align: center; font-size: 0.6rem; font-weight: bold;">{nom_eq}</td>'
            else:
                html_sup += '<td style="border: 1px solid #ddd; padding: 2px; background-color: white;"></td>'
        
        html_sup += "</tr>"
    
    html_sup += "</tbody></table></div>"
    
    st.markdown(html_sup, unsafe_allow_html=True)
    
    # Petite légende
    st.caption("💡 Astuce : Sur mobile, faites glisser le tableau vers la droite pour voir tous les locaux.")

elif menu == "🔍 Rechercher":
    st.markdown("<h1>🔍 Rechercher par Équipe</h1>", unsafe_allow_html=True)
    
    # Zone de recherche
    nom_cherche = st.text_input("Entrez le nom de l'équipe", "").upper()
    
    if nom_cherche:
        # On s'assure que les noms de colonnes correspondent (Equipe, Date_DT)
        mask = (
            (df['Equipe'].str.contains(nom_cherche, na=False, case=False)) &
            (df['Date_DT'].dt.isocalendar().week == semaine_sel) &
            (df['Date_DT'].dt.year == annee_sel)
        )
        resultats = df[mask].sort_values(by=['Date_DT', 'Horaire'])

        if not resultats.empty:
            st.success(f"Nombre de créneau(x) trouvé(s) : {len(resultats)}")
            
            for idx, r in resultats.iterrows():
                with st.container():
                    col_sim, col_info = st.columns([0.2, 0.8])
                    # Utilisation de .get() pour éviter un plantage si le local est mal écrit
                    color = LOCAL_CONFIG.get(str(r['Local']).strip().upper(), "#333")
                    
                    col_sim.markdown(f"""
                        <div style="background-color:{color}; height:60px; border-radius:10px; 
                        border:2px solid black; display:flex; align-items:center; justify-content:center;">
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # CORRECTION ICI : r['Date_DT'] au lieu de r['Date']
                    # On affiche la date proprement avec .strftime
                    date_str = r['Date_DT'].strftime('%d/%m/%Y')
                    
                    col_info.markdown(f"""
                        **{date_str}** — <span style="color:{color}; font-weight:bold;">{r['Local']}</span><br>
                        ⌚ **{r['Horaire']}**
                        """, unsafe_allow_html=True)
                    st.divider()
        else:
            st.warning(f"Aucune réservation trouvée pour '{nom_cherche}' en semaine {semaine_sel}.")
    else:
        st.info("Saisissez un nom pour voir votre planning de la semaine.")

elif menu == "📊 Statistiques":
    st.markdown("<h1>📊 Statistiques</h1>", unsafe_allow_html=True)
    if not df.empty:
        def calcul_duree(horaire_str):
            h_deb, h_fin = extraire_heures(horaire_str)
            return (h_fin - h_deb) if h_deb is not None else 0
        df['Duree_H'] = df['Horaire'].apply(calcul_duree)
        df['Mois'] = df['Date_DT'].dt.strftime('%m - %B')
        df['Annee'] = df['Date_DT'].dt.year

        st.subheader("📁 Volume horaire par équipe (Mensuel)")
        mois_dispo = sorted(df['Mois'].unique())
        mois_sel = st.selectbox("Mois", mois_dispo, index=len(mois_dispo)-1)
        stats_equipe = df[df['Mois'] == mois_sel].groupby('Equipe')['Duree_H'].sum().reset_index()
        st.dataframe(stats_equipe.sort_values(by='Duree_H', ascending=False), use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("🖥️ Utilisation des locaux (Annuel)")
        stats_local = df[df['Annee'] == annee_sel].groupby('Local')['Duree_H'].sum().sort_values(ascending=False)
        st.bar_chart(stats_local)
    else:
        st.warning("Aucune donnée.")

elif menu == "🎯 Assignation Responsables":
    st.header(f"🎯 Responsables - Semaine {semaine_sel}")
    
    # 1. Liste des animateurs (A ajuster selon tes besoins)
    ANIMATEURS = ["-- Choisir --", "MAX", "ALEKS", "ALEX", "MAEL", "ELIES", "LISE", "SIMON", "JOSS"]
    
    # 2. Préparation des données de la semaine
    jours_semaine = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    jours_trad = {"Lundi": 0, "Mardi": 1, "Mercredi": 2, "Jeudi": 3, "Vendredi": 4}
    
    # On crée 5 onglets pour les jours de la semaine
    onglets = st.tabs(jours_semaine)

    for i, jour in enumerate(jours_semaine):
        with onglets[i]:
            # Calcul de la date précise pour le jour de l'onglet
            base_semaine = pd.to_datetime(f"{annee_sel}-W{semaine_sel}-1", format="%G-W%V-%u")
            date_cible = (base_semaine + pd.Timedelta(days=jours_trad[jour])).date()
            date_str_iso = date_cible.strftime("%Y-%m-%d") # Format pour le filtre Supabase
            
            # Affichage de la date
            st.subheader(f"📅 {jour} {date_cible.strftime('%d/%m')}")

            # Filtrer le DataFrame pour ce jour précis
            mask_jour = (df['Date_DT'].dt.date == date_cible)
            activites_du_jour = df[mask_jour].sort_values(by='Horaire')

            if activites_du_jour.empty:
                st.info("Aucun créneau prévu pour ce jour.")
            else:
                # INITIALISATION DU FORMULAIRE PAR JOUR
                with st.form(key=f"form_assign_{jour}"):
                    updates_a_envoyer = []

                    # On boucle sur chaque réservation du jour
                    for _, row in activites_du_jour.iterrows():
                        equipe = row.get('Equipe', 'Inconnu')
                        local = row.get('Local', 'Inconnu')
                        horaire = row.get('Horaire', 'Inconnu')
                        current_resp = str(row.get('Responsable', '')).strip()
                        row_id = row.get('id')

                        # Nettoyage du responsable actuel pour la selectbox
                        if not current_resp or current_resp == "nan" or current_resp == "None":
                            current_resp = "-- Choisir --"

                        # Calcul de l'index par défaut
                        def_idx = ANIMATEURS.index(current_resp) if current_resp in ANIMATEURS else 0

                        # Affichage du créneau avec sa selectbox
                        st.markdown(f"**🕒 {horaire}** | 🏠 **{local}** — 👥 *{equipe}*")
                        resp_choisi = st.selectbox(
                            f"Responsable pour {local} {horaire}",
                            ANIMATEURS,
                            index=def_idx,
                            key=f"sel_{row_id}_{jour}", # Clé unique basée sur l'ID Supabase
                            label_visibility="collapsed"
                        )
                        
                        # On stocke les changements si un responsable est choisi
                        updates_a_envoyer.append({
                            "id": row_id,
                            "responsable": resp_choisi if resp_choisi != "-- Choisir --" else ""
                        })
                    
                    st.divider()
                    btn_save = st.form_submit_button(f"💾 ENREGISTRER LE {jour.upper()}", use_container_width=True)
                    
                    # LOGIQUE DE MISE À JOUR SUPABASE
                    if btn_save:
                        try:
                            with st.spinner("Mise à jour en cours..."):
                                for upd in updates_a_envoyer:
                                    # Mise à jour ligne par ligne via l'ID unique
                                    supabase.table("Planning").update({
                                        "responsable": upd["responsable"]
                                    }).eq("id", upd["id"]).execute()
                                
                                st.success(f"✅ Responsables enregistrés pour le {jour} !")
                                st.cache_data.clear() # Vider le cache pour rafraîchir le planning global
                                time.sleep(1)
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur lors de l'enregistrement : {e}")

elif menu == "🔐 Administration":
    st.markdown("<h1>⚙️ Gestion des Réservations</h1>", unsafe_allow_html=True)
    
    if is_admin:
        tab1, tab2, tab3 = st.tabs(["➕ Ajouter", "📝 Modifier", "🗑️ Supprimer"])
        
        # Filtrage des données pour la semaine sélectionnée
        df_filtre_admin = df[
            (df['Date_DT'].dt.isocalendar().week == semaine_sel) & 
            (df['Date_DT'].dt.year == annee_sel)
        ].sort_values(by=['Date_DT', 'Horaire'])
        
        with tab1:
            with st.form("ajouter_form", clear_on_submit=True):
                d_add = st.date_input("Date", value=datetime.now())
                eq_add = st.text_input("Equipe", placeholder="Nom")
                hr_add = st.text_input("Horaire", placeholder="08h00 - 10h00")
                lc_add = st.selectbox("Local", list(LOCAL_CONFIG.keys()), index=list(LOCAL_CONFIG.keys()).index(local_sel))
                
                if st.form_submit_button("Vérifier et Ajouter"):
                    if eq_add and hr_add:
                        status, msg = verifier_conflit(df, d_add, hr_add, lc_add, eq_add)
                        
                        if status == "block":
                            st.error(f"❌ {msg}")
                        else:
                            try:
                                db_add(d_add, eq_add, hr_add, lc_add)
                                st.success("✅ Réservation validée !")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur Supabase : {e}")
                    else:
                        st.warning("Veuillez remplir tous les champs.")

        with tab2:
            if not df_filtre_admin.empty:
                # Sélection par ID pour être précis avec Supabase
                idx_sel = st.selectbox("Sélectionner le créneau", df_filtre_admin.index, 
                                     format_func=lambda i: f"{df.loc[i,'Date_DT'].strftime('%d/%m')} | {df.loc[i,'Equipe']} ({df.loc[i,'Horaire']})")
                
                with st.form("modifier_form"):
                    ed = st.date_input("Date", value=df.loc[idx_sel,'Date_DT'])
                    ee = st.text_input("Equipe", df.loc[idx_sel,'Equipe'])
                    eh = st.text_input("Horaire", df.loc[idx_sel,'Horaire'])
                    es = st.selectbox("Local", list(LOCAL_CONFIG.keys()), 
                                    index=list(LOCAL_CONFIG.keys()).index(str(df.loc[idx_sel,'Local']).strip().upper()))
                    
                    if st.form_submit_button("Enregistrer les modifications"):
                        try:
                            # Utilisation de l'ID unique de la ligne
                            row_id = df.loc[idx_sel, 'id']
                            db_update(row_id, ed, ee, eh, es)
                            st.success("📝 Modification enregistrée !")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur de modification : {e}")
            else:
                st.warning("Aucun créneau à modifier cette semaine.")

        with tab3:
            if not df_filtre_admin.empty:
                t_del_idx = st.selectbox("Créneau à supprimer", df_filtre_admin.index, 
                                       format_func=lambda i: f"{df.loc[i,'Date_DT'].strftime('%d/%m')} | {df.loc[i,'Equipe']} - {df.loc[i,'Local']} ({df.loc[i,'Horaire']})")
                
                if st.button("❌ Supprimer définitivement", disabled=not st.checkbox("Confirmer la suppression")):
                    try:
                        row_id = df.loc[t_del_idx, 'id']
                        db_delete(row_id)
                        st.success("🗑️ Supprimé !")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur de suppression : {e}")
            else:
                st.warning("Aucun créneau à supprimer cette semaine.")
    else:
        st.error("🔒 Accès réservé. Veuillez saisir le mot de passe dans la barre latérale.")
        st.info("L'administration permet d'ajouter, modifier ou supprimer des créneaux de manière avancée.")
