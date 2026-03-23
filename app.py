import streamlit as st
import pandas as pd
import requests
import time
import re
import json
import io
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="IO", layout="wide", initial_sidebar_state="expanded")

# --- 2. INITIALISATION DE LA SESSION ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

# --- 3. LOGIQUE VISUELLE DE CONNEXION ---
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
            # Dictionnaire des accès avec rôles
            credentials = {
                "UT": {"pw": "Azerty123*", "role": "Utilisateur"},
                "ANIM": {"pw": "Anim2026*", "role": "Animateur"}
            }
            
            if user_input in credentials and pw_input == credentials[user_input]["pw"]:
                st.session_state["auth"] = True
                st.session_state["role"] = credentials[user_input]["role"]
                st.success(f"Accès en tant qu'{st.session_state['role']}")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Identifiants incorrects")
    st.stop()
    
# --- 4. SI CONNECTÉ : DESIGN NORMAL ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    header { visibility: visible !important; }
    [data-testid="stSidebar"] { 
        visibility: visible !important;
        background-color: #E2E8F0 !important; 
        border-right: 2px solid #000000 !important; 
    }
    .st-emotion-cache-6q9sum.ef3ps4o4 { fill: #0026C7 !important; }
    </style>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
    <div style="background: linear-gradient(90deg, #0026C7 0%, #FFFFFF 40%, #FFFFFF 60%, #C70000 100%); 
                padding: 3px; border-radius: 3px; text-align: center; width: 50%; margin: 0 auto;">
        <p style="font-size: 9px !important; color: black; margin: 0; letter-spacing: 1px; text-transform: uppercase; font-family: 'Impact';">
            ⌬ IO
        </p>
    </div>
    <br>
""", unsafe_allow_html=True
)

# --- 5. LOGIQUE DE CONNEXION ---
if not st.session_state["auth"]:
    st.markdown("### ⌬ Accès IO")
    with st.form("login_form"):
        user_input = st.text_input("Identifiant")
        pw_input = st.text_input("Mot de passe", type="password")
        submit_auth = st.form_submit_button("Se connecter")
        
        if submit_auth:
            # Remplace par tes vrais identifiants
            if user_input == "UT" and pw_input == "Azerty123*":
                st.session_state["auth"] = True
                st.success("Connexion réussie !")
                st.rerun()
            else:
                st.error("Identifiants incorrects")
    st.stop() # Arrête le script ici tant qu'on n'est pas connecté

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


# --- CONFIGURATION FIXE ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1mmPHzEY9p7ohdzvIYvwQOvqmKNa_8VQdZyl4sj1nksw/export?format=csv&gid=0"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxhetuY5QpJEvl-Wv1BMGej5FeW6S3-WDcbS1DwcwUVT-Yt3e8th1XG9pPCcbrwPu5ITw/exec"
ADMIN_PASSWORD = "1234" 

LOCAL_CONFIG = {
    "JUP": "#1976D2", "MIN": "#C2185B", "JUN": "#757575",
    "BAC": "#388E3C", "MARS": "#D32F2F", "SAT": "#E65100",
    "CRO": "#A1887F", "NEK": "#C5A000", "PHO": "#DAA520",
    "PERS": "#558B2F", "SAG": "#4A148C"
}

# Liste arrêtée à 20:00 pile pour supprimer la ligne 20:30
QUARTS_HEURES = [f"{h:02d}:{m}" for h in range(6, 20) for m in ["00", "30"]] + ["20:00"]

st.set_page_config(page_title="Planning", layout="wide")

# --- LOGIQUE DONNÉES ---
def extraire_heures(horaire_str):
    try:
        nums = re.findall(r'(\d+)', str(horaire_str))
        if len(nums) >= 4:
            h_deb = int(nums[0]) + int(nums[1])/60
            h_fin = int(nums[2]) + int(nums[3])/60
            return h_deb, h_fin
    except: pass
    return None, None

def formater_heure_propre(texte):
    # Remplace les points ou virgules par des 'h'
    texte = texte.lower().replace('.', 'h').replace(':', 'h').replace(' ', '')
    # Si l'utilisateur a juste écrit "08h10h", on essaie de reconstruire "08h00 - 10h00"
    # C'est une sécurité bonus pour ton Google Sheets
    return texte

def verifier_conflit(df, date_test, horaire_test, local_test, equipe_test, exclude_idx=None):
    h_deb_new, h_fin_new = extraire_heures(horaire_test)
    if h_deb_new is None: return "block", "Format d'heure invalide."
    
    date_test_dt = pd.to_datetime(date_test)
    eq_test = str(equipe_test).strip().upper()
    
    # 1. Vérification local (Bloquant)
    match_local = df[(df['Date_DT'].dt.date == date_test_dt.date()) & 
                    (df['Local'].str.strip().str.upper() == local_test.upper())]
    for idx, row in match_local.iterrows():
        if exclude_idx is not None and idx == exclude_idx: continue
        h_deb_ex, h_fin_ex = extraire_heures(row['Horaire'])
        if h_deb_ex is not None and max(h_deb_new, h_deb_ex) < min(h_fin_new, h_fin_ex):
            return "block", f"ALERTE : Le local {local_test} est déjà pris par {row['Equipe']}."

    # 2. Vérification ÉQUIPE (Doublon autorisé avec confirmation)
    match_eq = df[(df['Date_DT'].dt.date == date_test_dt.date()) & 
                  (df['Equipe'].str.strip().str.upper() == eq_test)]
    for idx, row in match_eq.iterrows():
        if exclude_idx is not None and idx == exclude_idx: continue
        h_deb_ex, h_fin_ex = extraire_heures(row['Horaire'])
        if h_deb_ex is not None and max(h_deb_new, h_deb_ex) < min(h_fin_new, h_fin_ex):
            return "warn", f"DOUBLON : L'équipe {eq_test} est déjà sur {row['Simu']} à cette heure."

    return "ok", ""

@st.cache_data(ttl=2)
def load_data():
    try:
        url = f"{SHEET_CSV_URL}&v={time.time()}"
        data = pd.read_csv(url)
        data['Date_DT'] = pd.to_datetime(data['Date'], dayfirst=True, errors='coerce')
        return data.dropna(subset=['Date_DT', 'Horaire'])
    except: return pd.DataFrame()

# --- INTERFACE ---
df = load_data()
# --- 1. DÉFINITION DE LA LISTE DE BASE ---
# Accessible à tout le monde
menus_de_base = ["📅 Planning", "🖥️ Supervision", "🔍 Rechercher", "📊 Statistiques"]

# --- 2. LOGIQUE RÉSERVÉE À L'ANIMATEUR ---
if st.session_state.get("role") == "Animateur":
    # Insertion des options supplémentaires dans la liste
    menus_de_base.insert(4, "🎯 Assignation Responsables")
    menus_de_base.insert(4, "📋 Gestion Personnel")
    menus_de_base.insert(5, "🔐 Administration")

    # Affichage du menu principal
    menu = st.sidebar.radio("MENU", menus_de_base)

    # BLOC ACCÈS ADMIN (Visible uniquement pour l'Animateur)
    st.sidebar.markdown("---")
    st.sidebar.title("🔐 Accès ADMIN")
    admin_key = st.sidebar.text_input("Mot de passe", type="password", key="global_pwd")
    
    # Vérification de la clé
    is_admin = (admin_key == ADMIN_PASSWORD)
    if is_admin:
        st.sidebar.success("Mode Administrateur Actif")
    elif admin_key != "":
        st.sidebar.error("Mot de passe incorrecte")

else:
    # --- 3. AFFICHAGE POUR L'UTILISATEUR SIMPLE (UT) ---
    menu = st.sidebar.radio("MENU", menus_de_base)
    is_admin = False # Sécurité pour bloquer les fonctions admin

st.sidebar.divider()

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

st.sidebar.divider()
st.sidebar.subheader("📱 Options d'affichage")
mode_vue = st.sidebar.segmented_control("Format", ["Semaine", "Jour"], default="Jour")

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
    [data-testid="stSidebar"] {{ background-color: #E2E8F0 !important; border-right: 2px solid #000000 !important; }}
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
    st.markdown("<h1>🖥️ Vue d'ensemble des Locaux</h1>", unsafe_allow_html=True)
    
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
    nom_cherche = st.text_input("Entrez le nom de l'équipe (ex: ECOLE)", "").upper()
    
    if nom_cherche:
        # Filtrage sur le nom, l'année et la semaine sélectionnée en sidebar
        mask = (
            (df['Equipe'].str.contains(nom_cherche, na=False, case=False)) &
            (df['Date_DT'].dt.isocalendar().week == semaine_sel) &
            (df['Date_DT'].dt.year == annee_sel)
        )
        resultats = df[mask].sort_values(by=['Date_DT', 'Horaire'])

        if not resultats.empty:
            st.success(f"Nombre de créneau(x) trouvé(s) : {len(resultats)}")
            
            # Affichage sous forme de "Cartes" pour mobile
            for idx, r in resultats.iterrows():
                with st.container():
                    col_sim, col_info = st.columns([0.2, 0.8])
                    color = LOCAL_CONFIG.get(r['Local'].strip().upper(), "#333")
                    
                    # Petit carré de couleur du local
                    col_sim.markdown(f"""
                        <div style="background-color:{color}; height:60px; border-radius:10px; 
                        border:2px solid black; display:flex; align-items:center; justify-content:center;">
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Détails de la réservation
                    col_info.markdown(f"""
                        **{r['Date']}** — <span style="color:{color}; font-weight:bold;">{r['Local']}</span><br>
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
    
    ANIMATEURS = ["-- Choisir --", "MAX", "ALEKS", "ALEX", "MAEL", "ELIES", "LISE", "SIMON", "JOSS"]
    
    tous_les_locaux = sorted(df['Local'].unique())
    tous_les_horaires = sorted(df['Horaire'].unique())
    jours_semaine = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    jours_trad = {"Lundi": 0, "Mardi": 1, "Mercredi": 2, "Jeudi": 3, "Vendredi": 4}
    
    onglets = st.tabs(jours_semaine)

    for i, jour in enumerate(jours_semaine):
        with onglets[i]:
            base_semaine = pd.to_datetime(f"{annee_sel}-W{semaine_sel}-1", format="%G-W%V-%u")
            date_cible = (base_semaine + pd.Timedelta(days=jours_trad[jour])).date()
            
            # INITIALISATION DU FORMULAIRE
            with st.form(key=f"form_assign_{jour}"):
                st.subheader(f"📅 {jour} {date_cible.strftime('%d/%m')}")
                updates_a_envoyer = []

                for heure in tous_les_horaires:
                    # Filtrer les réservations pour ce jour et cette heure
                    mask_jour_heure = (df['Date_DT'].dt.date == date_cible) & (df['Horaire'] == heure)
                    activites_creneau = df[mask_jour_heure]

                    if not activites_creneau.empty:
                        st.markdown(f"#### 🕒 {heure}")
                        
                        for _, row in activites_creneau.iterrows():
                            # Vérification de l'équipe (Correction du .iloc ici via 'row')
                            if pd.notna(row['Equipe']) and row['Equipe'] not in ["Libre", ""]:
                                equipe = row['Equipe']
                                local = row['Local']
                                current_resp = str(row['Responsable']) if pd.notna(row['Responsable']) else "-- Choisir --"
                                
                                # Calcul de l'index pour la selectbox
                                def_idx = ANIMATEURS.index(current_resp) if current_resp in ANIMATEURS else 0

                                with st.container():
                                    st.write(f"🏠 **{local}** — 👥 *{equipe}*")
                                    resp_choisi = st.selectbox(
                                        f"Responsable {local} {heure}",
                                        ANIMATEURS,
                                        index=def_idx,
                                        key=f"sel_{date_cible}_{heure}_{local}",
                                        label_visibility="collapsed"
                                    )
                                    
                                    updates_a_envoyer.append({
                                        "date": str(date_cible),
                                        "horaire": str(heure),
                                        "local": str(local),
                                        "responsable": resp_choisi if resp_choisi != "-- Choisir --" else ""
                                    })
                
                # LE BOUTON DOIT ÊTRE À L'INTÉRIEUR DU "WITH ST.FORM"
                btn_save = st.form_submit_button(f"💾 ENREGISTRER LE {jour.upper()}", use_container_width=True)
                
                # LOGIQUE D'ENVOI (Après le clic sur le bouton)
                if btn_save:
                    if updates_a_envoyer:
                        try:
                            payload = {"action": "update_batch_responsables", "data": updates_a_envoyer}
                            response = requests.post(SCRIPT_URL, json=payload)
                            if "Success" in response.text:
                                st.success(f"✅ Mis à jour pour le {jour} !")
                                st.rerun()
                            else:
                                st.error(f"Erreur : {response.text}")
                        except Exception as e:
                            st.error(f"Erreur de connexion : {e}")

elif menu == "📋 Gestion Personnel":
    st.header("📋 Enregistrement Personnel (Col F-I)")
    
    with st.form("form_gestion_perso"):
        col1, col2 = st.columns(2)
        with col1:
            date_p = st.date_input("Date (Col F)")
            # Remplace la liste par tes vrais noms d'animateurs
            anim_p = st.selectbox("Animateur (Col G)", ["MAX", "ALEX", "SOPHIE", "LUCAS", "JULIE"])
        with col2:
            type_p = st.selectbox("Type (Col H)", ["Réunion", "Absence", "Formation", "Congé"])
            heure_p = st.text_input("Horaire (Col I)", placeholder="ex: 08h-10h")
            
        btn_perso = st.form_submit_button("ENREGISTRER")
        
        if btn_perso:
            payload = {
                "action": "add_personnel",
                "date": str(date_p),
                "animateur": anim_p,
                "type": type_p,
                "horaire": heure_p
            }
            try:
                response = requests.post(SCRIPT_URL, json=payload)
                if "Success" in response.text:
                    st.success(f"✅ Enregistré pour {anim_p} en colonnes F-I")
                else:
                    st.error(f"Erreur : {response.text}")
            except Exception as e:
                st.error(f"Erreur de connexion : {e}")

elif menu == "🔐 Administration":
    st.markdown("<h1>⚙️ Gestion des Réservations</h1>", unsafe_allow_html=True)
    
    # Plus besoin de 'pwd = st.sidebar.text_input...' ici !
    # On utilise directement la variable 'is_admin' définie plus haut
    
    if is_admin:
        tab1, tab2, tab3 = st.tabs(["➕ Ajouter", "📝 Modifier", "🗑️ Supprimer"])
        
        # Le reste de ton code d'administration (df_filtre_admin, etc.) continue ici...
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
            
            # Le bouton principal du formulaire
            if st.form_submit_button("Vérifier et Ajouter"):
                if eq_add and hr_add:
                    status, msg = verifier_conflit(df, d_add, hr_add, lc_add, eq_add)
                    
                    if status == "block":
                        st.error(f"❌ {msg}")
                    elif status == "warn":
                        st.warning(f"⚠️ {msg}")
                        # On mémorise les infos pour le bouton de confirmation qui est HORS du formulaire
                        st.session_state['confirm_add_doublon'] = {"date":d_add, "eq":eq_add, "hr":hr_add, "lc":lc_add}
                    else:
                        requests.post(SCRIPT_URL, data=json.dumps({"action":"add","date":d_add.strftime("%d/%m/%Y"),"equipe":eq_add.upper(),"horaire":hr_add,"local":lc_add}))
                        st.success("✅ Réservation validée !"), time.sleep(1), st.rerun()
                else:
                    st.warning("Veuillez remplir tous les champs.")

        # --- ICI ON EST HORS DU FORMULAIRE (aligné sur le 'with') ---
        if st.session_state.get('confirm_add_doublon'):
            st.info("ℹ️ Cliquez ci-dessous pour forcer l'ajout en doublon.")
            if st.button("👍 Confirmer le doublon volontaire", key="confirm_add"):
                conf = st.session_state['confirm_add_doublon']
                requests.post(SCRIPT_URL, data=json.dumps({
                    "action":"add",
                    "date":conf['date'].strftime("%d/%m/%Y"),
                    "equipe":conf['eq'].upper(),
                    "horaire":conf['hr'],
                    "local":conf['lc']
                }))
                del st.session_state['confirm_add_doublon'] # On nettoie la session
                st.success("✅ Doublon ajouté !"), time.sleep(1), st.rerun()
            
            else:
                st.warning("Veuillez remplir tous les champs.")

        with tab2:
            if not df_filtre_admin.empty:
                idx_mod = st.selectbox("Sélectionner le créneau", df_filtre_admin.index, format_func=lambda i: f"{df.loc[i,'Date']} | {df.loc[i,'Equipe']} ({df.loc[i,'Horaire']})")
                with st.form("modifier_form"):
                    ed = st.date_input("Date", value=df.loc[idx_mod,'Date_DT'])
                    ee = st.text_input("Equipe", df.loc[idx_mod,'Equipe'])
                    eh = st.text_input("Horaire", df.loc[idx_mod,'Horaire'])
                    es = st.selectbox("Local", list(LOCAL_CONFIG.keys()), index=list(LOCAL_CONFIG.keys()).index(str(df.loc[idx_mod,'Local']).strip().upper()))
                    if st.form_submit_button("Vérifier et Enregistrer"):
                        status, msg = verifier_conflit(df, ed, eh, es, ee, exclude_idx=idx_mod)
                        
                        if status == "block":
                            st.error(f"❌ MODIFICATION IMPOSSIBLE : {msg}")
                        elif status == "warn":
                            st.warning(f"⚠️ {msg}")
                            st.session_state['confirm_mod_doublon'] = {"row":int(idx_mod)+2, "date":ed, "eq":ee, "hr":eh, "sm":es}
                        else:
                            requests.post(SCRIPT_URL, data=json.dumps({"action":"update","row":int(idx_mod)+2,"date":ed.strftime("%d/%m/%Y"),"equipe":ee.upper(),"horaire":eh,"local":es}))
                            st.success("📝 Modification enregistrée !"), time.sleep(1), st.rerun()

                # Bouton de confirmation de modification pour l'admin
                if st.session_state.get('confirm_mod_doublon'):
                    if st.button("👍 Confirmer la modification en doublon"):
                        conf = st.session_state['confirm_mod_doublon']
                        requests.post(SCRIPT_URL, data=json.dumps({"action":"update","row":conf['row'],"date":conf['date'].strftime("%d/%m/%Y"),"equipe":conf['eq'].upper(),"horaire":conf['hr'],"local":conf['sm']}))
                        del st.session_state['confirm_mod_doublon']
                        st.success("📝 Modification forcée effectuée !"), time.sleep(1), st.rerun()
            else:
                st.warning("Aucun créneau à modifier cette semaine.")

        with tab3:
            if not df_filtre_admin.empty:
                t_del = st.selectbox("Créneau à supprimer", df_filtre_admin.index, format_func=lambda i: f"{df.loc[i,'Date']} | {df.loc[i,'Equipe']} ({df.loc[i,'Horaire']}) {df.loc[i,'Local']}")
                if st.button("❌ Supprimer définitivement", disabled=not st.checkbox("Confirmer")):
                    requests.post(SCRIPT_URL, data=json.dumps({"action":"delete","row":int(t_del)+2}))
                    st.success("🗑️ Supprimé !"), time.sleep(1), st.rerun()
    else:
        # Message si l'utilisateur n'est pas admin
        st.error("🔒 Accès réservé. Veuillez saisir le mot de passe dans la barre latérale pour accéder à la gestion.")
        st.info("L'administration permet d'ajouter, modifier ou supprimer des créneaux de manière avancée.")
       
