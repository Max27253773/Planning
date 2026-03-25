import streamlit as st
import pandas as pd
import time
import re
from datetime import datetime, timedelta
from supabase import create_client

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
        # Changement ici : "Planning" au lieu de "planning"
        response = supabase.table("Planning").select("*").execute()
        data = pd.DataFrame(response.data)
        if not data.empty:
            data['Date_DT'] = pd.to_datetime(data['date'], errors='coerce')
            data = data.rename(columns={
                "equipe": "Equipe", "horaire": "Horaire", "local": "Local", 
                "responsable": "Responsable", "date": "Date"
            })
            return data
        return pd.DataFrame(columns=["id", "Date", "Equipe", "Horaire", "Local", "Responsable", "Date_DT"])
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
    if h_deb_new is None: return "block", "Format d'heure invalide (ex: 08:00 - 10:00)."
    date_s = str(date_test)
    # Vérification occupation du local
    mask = (df['Date'] == date_s) & (df['Local'].str.upper() == local_test.upper())
    if exclude_id: mask = mask & (df['id'] != exclude_id)
    for _, row in df[mask].iterrows():
        h_ex_d, h_ex_f = extraire_heures(row['Horaire'])
        if h_ex_d is not None and max(h_deb_new, h_ex_d) < min(h_fin_new, h_ex_f):
            return "block", f"Le local {local_test} est déjà occupé sur ce créneau."
    return "ok", ""

# --- 4. AUTHENTIFICATION ---
if "auth" not in st.session_state: st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.markdown("""<style>[data-testid="stSidebar"] { visibility: hidden; } .main .block-container { max-width: 400px; margin: auto; padding-top: 5rem; }</style>""", unsafe_allow_html=True)
    with st.form("login"):
        st.subheader("CONNEXION IO")
        u = st.text_input("Identifiant")
        p = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("VALIDER"):
            creds = {"UT": "Azerty123*", "ANIM": "Anim2026*"}
            if u in creds and p == creds[u]:
                st.session_state["auth"], st.session_state["role"] = True, ("Animateur" if u=="ANIM" else "Utilisateur")
                st.rerun()
            else: st.error("Identifiants incorrects")
    st.stop()

# --- 5. CONFIGURATION VISUELLE ---
LOCAL_CONFIG = {
    "JUP": "#1976D2", "MIN": "#C2185B", "JUN": "#757575", "BAC": "#388E3C", 
    "MARS": "#D32F2F", "SAT": "#E65100", "CRO": "#A1887F", "NEK": "#C5A000", 
    "PHO": "#DAA520", "PERS": "#558B2F", "SAG": "#4A148C"
}
QUARTS_HEURES = [f"{h:02d}:{m}" for h in range(6, 21) for m in ["00", "30"]]

# --- INTERFACE ---
df = load_data()
# --- 1. DÉFINITION DE LA LISTE DE BASE ---
# Accessible à tout le monde
menus_de_base = ["📅 Planning", "🖥️ Supervision", "🔍 Rechercher", "📊 Statistiques"]

# --- 2. LOGIQUE RÉSERVÉE À L'ANIMATEUR ---
if st.session_state.get("role") == "Animateur":
    # Insertion des options supplémentaires dans la liste
    menus_de_base.insert(4, "🎯 Assignation Responsables")
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
jours_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
choix_j = st.sidebar.selectbox("Jour", jours_fr, index=min(maintenant.weekday(), 4) if annee_sel == maintenant.year else 0)
local_sel = st.sidebar.selectbox("Local", list(LOCAL_CONFIG.keys()))

st.sidebar.divider()
mode_vue = st.sidebar.segmented_control("Format", ["Semaine", "Jour"], default="Jour")

# Calcul de la date précise
monday = (datetime(annee_sel, 1, 4) - timedelta(days=datetime(annee_sel, 1, 4).weekday())) + timedelta(weeks=semaine_sel-1)
week_days = [monday + timedelta(days=i) for i in range(5)]
d_active = week_days[jours_fr.index(choix_j)]

# --- 7. CSS & DESIGN ---
current_color = LOCAL_CONFIG.get(local_sel, "#333")
st.markdown(f"""
    <style>
    .planning-frame {{ position: relative; width: 100%; height: 1260px; border: 1px solid #000; overflow: hidden; background: white; }}
    .hour-row-fixed {{ position: absolute; left: 0; right: 0; height: 45px; display: flex; align-items: center; border-bottom: 1px dashed #CCC; }}
    .calendar-cell-unique {{ 
        position: absolute; z-index: 100; border: 2px solid #000; color: white; 
        text-align: center; font-weight: 900; display: flex; align-items: center; 
        justify-content: center; box-shadow: 2px 2px 0px black; 
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 8. LOGIQUE DES PAGES ---

if menu == "📅 Planning":
    # --- 1. PRÉPARATION DES DONNÉES ---
    # On filtre le dataframe pour le local sélectionné
    df_view = df[df['Local'] == local_sel].copy()
    
    # On s'assure que Date_DT est bien au format datetime
    df_view['Date_DT'] = pd.to_datetime(df_view['Date_DT'], errors='coerce')
    
    # Définition des couleurs (à adapter selon tes goûts)
    current_color = "#3498db" # Bleu par défaut
    text_on_color = "white"

    # Récupération des dates de la semaine choisie
    # (On recalcule week_days ici pour être sûr qu'il existe)
    import datetime
    d_start = datetime.date.fromisocalendar(annee_sel, semaine_sel, 1)
    week_days = [d_start + datetime.timedelta(days=i) for i in range(5)]

    st.markdown(f"<h1 style='text-align:center;'>🏠 {local_sel}</h1>", unsafe_allow_html=True)
    
    # Sélecteur de mode (Jour/Semaine) si tu ne l'as pas déjà dans la sidebar
    mode_vue = st.radio("Mode d'affichage", ["Jour", "Semaine"], horizontal=True)

    if mode_vue == "Jour":
        # On utilise choix_j (défini dans la sidebar)
        d = week_days[jours_fr.index(choix_j)]
        
        st.markdown(f"<div style='text-align:center; background-color:{current_color}; color:{text_on_color}; padding:8px; font-weight:900; border:2px solid black; box-shadow: 2px 2px 0px black; margin-bottom:10px;'>{choix_j} {d.strftime('%d/%m')}</div>", unsafe_allow_html=True)
        
        # --- DESSIN DU PLANNING JOUR ---
        html_jour = '<div class="planning-frame" style="position:relative; height:1300px; background:#F0F2F6; border:1px solid #ddd;">'
        
        # On génère les lignes de temps (Quarts d'heure)
        for i, q in enumerate(QUARTS_HEURES):
            if i >= 29: break # Limite l'affichage à la journée
            top = i * 45
            style = "border-bottom: 2px solid #333;" if q.endswith(":00") else ""
            html_jour += f'<div class="hour-row-fixed" style="position:absolute; top:{top}px; left:0; right:0; height:45px; {style}"><div style="width:60px; text-align:right; padding-right:8px; font-weight:900; border-right:3px solid {current_color}; background:#F0F2F6; height:100%; display:flex; align-items:center; justify-content:flex-end; color:black;">{q}</div></div>'
        
        # On place les réservations
        resas = df_view[df_view['Date_DT'].dt.date == d]
        for _, r in resas.iterrows():
            h_deb, h_f = extraire_heures(r['Horaire']) # Vérifie que cette fonction existe
            if h_deb is not None:
                top_p = int((h_deb - 8) * 180) # Ajuste le décalage selon ton heure de début (ex: 8h)
                haut = int((h_f - h_deb) * 180) - 2
                html_jour += f'<div style="position:absolute; top:{top_p}px; height:{haut}px; left:65px; right:5px; background-color:{current_color}; color:white; padding:5px; border-radius:4px; font-size:14px; border:1px solid black; z-index:10;">{r["Equipe"]}</div>'
        
        st.markdown(html_jour + '</div>', unsafe_allow_html=True)

# --- 6. NAVIGATION & SIDEBAR ---
df = load_data()

# Gestion des menus selon le rôle
menus = ["📅 Planning", "🖥️ Supervision", "🔍 Rechercher", "📊 Statistiques"]
if st.session_state.get("role") == "Animateur":
    menus += ["🎯 Assignation Responsables", "🔐 Administration"]

menu = st.sidebar.radio("MENU", menus)
st.sidebar.divider()

# --- BLOC ACCÈS ADMIN (Sidebar) ---
is_admin = False
if st.session_state.get("role") == "Animateur":
    st.sidebar.title("🔐 Accès ADMIN")
    admin_key = st.sidebar.text_input("Mot de passe", type="password", key="global_pwd")
    if admin_key == ADMIN_PASSWORD:
        is_admin = True
        st.sidebar.success("Mode Administrateur Actif")
    elif admin_key != "":
        st.sidebar.error("Mot de passe incorrect")

st.sidebar.divider()

# --- CALCUL AUTOMATIQUE DATE/SEMAINE ---
maintenant = datetime.now()
jours_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]

annee_sel = st.sidebar.selectbox("Année",, index=1)
semaine_sel = st.sidebar.selectbox("Semaine", list(range(1, 54)), index=maintenant.isocalendar()-1)
choix_j = st.sidebar.selectbox("Jour", jours_fr, index=min(maintenant.weekday(), 4) if annee_sel == maintenant.year else 0)
local_sel = st.sidebar.selectbox("Local", list(LOCAL_CONFIG.keys()))

# --- RÉCUPÉRATION DES DATES DE LA SEMAINE ---
d_start = datetime.fromisocalendar(annee_sel, semaine_sel, 1).date()
week_days = [d_start + timedelta(days=i) for i in range(5)]

# --- 7. LOGIQUE D'AFFICHAGE DU PLANNING ---
if menu == "📅 Planning":
    st.markdown(f"<h1 style='text-align:center;'>🏠 {local_sel}</h1>", unsafe_allow_html=True)
    
    mode_vue = st.radio("Vue", ["Jour", "Semaine"], horizontal=True)
    
    # Filtrage des données pour le local
    df_view = df[df['Local'] == local_sel].copy()
    df_view['Date_DT'] = pd.to_datetime(df_view['Date_DT'], errors='coerce')
    
    current_color = "#3498db"
    text_on_color = "white"

    if mode_vue == "Jour":
        # Sélection du jour via la sidebar
        idx_jour = jours_fr.index(choix_j)
        d_active = week_days[idx_jour]
        
        st.markdown(f"<div style='text-align:center; background-color:{current_color}; color:{text_on_color}; padding:10px; font-weight:900; border:2px solid black; box-shadow: 3px 3px 0px black; margin-bottom:15px;'>{choix_j.upper()} {d_active.strftime('%d/%m')}</div>", unsafe_allow_html=True)
        
        # --- DESSIN DU PLANNING HTML ---
        html_jour = '<div style="position:relative; height:1305px; background:#F0F2F6; border:1px solid #ddd; overflow:hidden;">'
        
        # Quadrillage des heures (8h00 à 22h00 par exemple)
        for i, q in enumerate(QUARTS_HEURES):
            if i >= 60: break # Limite à la journée de travail
            top = i * 45
            is_pile = q.endswith(":00")
            line_style = "border-bottom: 2px solid #333;" if is_pile else "border-bottom: 1px dashed #ccc;"
            html_jour += f'''
                <div style="position:absolute; top:{top}px; left:0; right:0; height:45px; {line_style} display:flex; align-items:center;">
                    <div style="width:65px; text-align:right; padding-right:10px; font-weight:900; color:#555; background:#eee; height:100%; display:flex; align-items:center; justify-content:flex-end;">{q}</div>
                </div>
            '''
        
        # Placement des réservations
        resas = df_view[df_view['Date_DT'].dt.date == d_active]
        for _, r in resas.iterrows():
            h_deb, h_f = extraire_heures(r['Horaire'])
            if h_deb is not None:
                # Calcul de la position (ajuster le -8 si ton QUARTS_HEURES commence avant 8h)
                top_p = int((h_deb - 8) * 180) 
                hauteur = int((h_f - h_deb) * 180) - 4
                html_jour += f'''
                    <div style="position:absolute; top:{top_p}px; height:{hauteur}px; left:75px; right:10px; background:{current_color}; color:white; border:2px solid black; border-radius:5px; padding:8px; font-size:14px; font-weight:bold; z-index:10; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);">
                        {r["Equipe"]}
                    </div>
                '''
        
        st.markdown(html_jour + '</div>', unsafe_allow_html=True)

        # --- QUICK BOOKING (ADMIN UNIQUEMENT) ---
        if is_admin:
            st.divider()
            with st.expander("⚡ RÉSERVATION RAPIDE", expanded=False):
                with st.form("quick_booking"):
                    c1, c2 = st.columns(2)
                    q_eq = c1.text_input("Équipe", placeholder="Ex: EQUIPE A")
                    q_hr = c2.text_input("Horaire", placeholder="Ex: 10h00 - 12h00")
                    force_confirm = st.checkbox("Autoriser le doublon")
                    
                    if st.form_submit_button("Valider la réservation"):
                        if q_eq and q_hr:
                            # Vérification (doit être adaptée à ton format de données)
                            status, msg = verifier_conflit(df, d_active, q_hr, local_sel, q_eq)
                            
                            if status == "block":
                                st.error(msg)
                            elif status == "warn" and not force_confirm:
                                st.warning(msg)
                            else:
                                # INSERTION SUPABASE
                                new_data = {
                                    "Date_DT": d_active.strftime("%Y-%m-%d"),
                                    "Equipe": q_eq.upper(),
                                    "Horaire": q_hr,
                                    "Local": local_sel
                                }
                                try:
                                    supabase.table("PLANNING").insert(new_data).execute()
                                    st.success("Réservation enregistrée !")
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erreur Supabase : {e}")
                        else:
                            st.warning("Remplissez tous les champs.")

elif menu == "🖥️ Supervision":
    st.title("🖥️ Supervision des Locaux")
    df_jour = df[df['Date'] == str(d_active.date())]
    if not df_jour.empty:
        st.dataframe(df_jour[['Horaire', 'Local', 'Equipe', 'Responsable']], use_container_width=True, hide_index=True)
    else:
        st.write("Aucune réservation aujourd'hui.")

elif menu == "🔍 Rechercher":
    st.title("🔍 Rechercher une équipe")
    query = st.text_input("Nom de l'équipe").upper()
    if query:
        res = df[df['Equipe'].str.contains(query, na=False)]
        st.table(res[['Date', 'Horaire', 'Local', 'Responsable']])

elif menu == "📊 Statistiques":
    st.title("📊 Statistiques d'utilisation")
    if not df.empty:
        stats = df.groupby('Local').size()
        st.bar_chart(stats)

elif menu == "🎯 Assignation Responsables" and st.session_state["role"] == "Animateur":
    st.title("🎯 Assignation des Responsables")
    ANIMATEURS = ["MAX", "ALEKS", "ALEX", "MAEL", "ELIES", "LISE", "SIMON", "JOSS"]
    
    df['Date_DT'] = pd.to_datetime(df['Date_DT'], errors='coerce')
    df_week = df[df['Date_DT'].dt.isocalendar().week == semaine_sel].sort_values(['Date_DT', 'Horaire'])
    
    for _, row in df_week.iterrows():
        c1, c2 = st.columns()
        c1.write(f"**{row['Date']}** | {row['Horaire']} | {row['Equipe']} ({row['Local']})")
        idx_res = ANIMATEURS.index(row['Responsable']) if row['Responsable'] in ANIMATEURS else 0
        new_r = c2.selectbox("Resp", ANIMATEURS, index=idx_res, key=f"r_{row['id']}")
        if new_r != row['Responsable']:
            db_update_resp(row['id'], new_r)
            st.rerun()

elif menu == "🔐 Administration" and st.session_state["role"] == "Animateur":
    st.title("⚙️ Administration (Supabase)")
    t1, t2, t3 = st.tabs(["Ajouter", "Modifier", "Supprimer"])
    
    with t1:
        with st.form("admin_add"):
            d_a = st.date_input("Date", value=d_active)
            e_a = st.text_input("Equipe")
            h_a = st.text_input("Horaire", placeholder="08:00 - 10:00")
            l_a = st.selectbox("Local", list(LOCAL_CONFIG.keys()))
            if st.form_submit_button("VALIDER"):
                status, msg = verifier_conflit(df, d_a, h_a, l_a, e_a)
                if status == "ok":
                    db_add(d_a, e_a, h_a, l_a)
                    st.success("Ajouté !"); time.sleep(1); st.rerun()
                else: st.error(msg)
                
    with t2:
        if not df.empty:
            sel_mod = st.selectbox("Ligne à modifier", df['id'].tolist(), format_func=lambda x: f"{df[df['id']==x]['Date'].values} - {df[df['id']==x]['Equipe'].values}")
            row_mod = df[df['id'] == sel_mod].iloc
            with st.form("admin_edit"):
                new_e = st.text_input("Equipe", row_mod['Equipe'])
                new_h = st.text_input("Horaire", row_mod['Horaire'])
                if st.form_submit_button("MODIFIER"):
                    db_update(sel_mod, row_mod['Date'], new_e, new_h, row_mod['Local'])
                    st.success("Modifié !"); time.sleep(1); st.rerun()

    with t3:
        sel_del = st.selectbox("Ligne à supprimer", df['id'].tolist(), key="del_box")
        if st.button("SUPPRIMER DÉFINITIVEMENT", type="primary"):
            db_delete(sel_del)
            st.success("Supprimé !"); time.sleep(1); st.rerun()
