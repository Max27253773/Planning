import streamlit as st
import pandas as pd
import requests
import time
import json
import re

# --- CONFIGURATION ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1mmPHzEY9p7ohdzvIYvwQOvqmKNa_8VQdZyl4sj1nksw/export?format=csv&gid=0"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxhetuY5QpJEvl-Wv1BMGej5FeW6S3-WDcbS1DwcwUVT-Yt3e8th1XG9pPCcbrwPu5ITw/exec"

st.set_page_config(page_title="Planning Simu Pro", layout="wide")
st.title("✈️ Gestion & Suivi des Heures")

# --- LOGIQUE DE CALCUL PRÉCISE (Minutes comprises) ---
def extraire_heures_precises(horaire_str):
    """Calcule la durée précise même avec des minutes (ex: '13h30 - 17h00' -> 3.5)"""
    try:
        # On cherche tous les blocs de chiffres (heures et minutes)
        # Format attendu : "13h30 - 17h00" ou "13:30 - 17:00"
        blocs = re.findall(r'(\d+)[h:]?(\d+)?', str(horaire_str))
        
        if len(blocs) >= 2:
            # Heure de début
            h1 = int(blocs[0][0])
            m1 = int(blocs[0][1]) if blocs[0][1] else 0
            
            # Heure de fin
            h2 = int(blocs[1][0])
            m2 = int(blocs[1][1]) if blocs[1][1] else 0
            
            # Conversion en minutes totales depuis minuit
            debut_minutes = (h1 * 60) + m1
            fin_minutes = (h2 * 60) + m2
            
            # Calcul de la durée en heures décimales
            duree_heures = (fin_minutes - debut_minutes) / 60
            return round(abs(duree_heures), 2)
        
        # Si un seul nombre est présent (ex: "4h")
        nombres_seuls = re.findall(r'\d+', str(horaire_str))
        if len(nombres_seuls) == 1:
            return float(nombres_seuls[0])
            
        return 4.0 # Valeur par défaut
    except:
        return 4.0

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data(ttl=2)
def load_data():
    try:
        url_force = f"{SHEET_CSV_URL}&v={time.time()}"
        data = pd.read_csv(url_force)
        data['Date_DT'] = pd.to_datetime(data['Date'], errors='coerce')
        data['Annee'] = data['Date_DT'].dt.year.fillna(0).astype(int)
        # Nouveau calcul précis
        data['Heures'] = data['Horaire'].apply(extraire_heures_precises)
        return data
    except:
        return pd.DataFrame(columns=["Date", "Equipage", "Horaire", "Simu", "Annee", "Heures"])

df = load_data()

# --- BARRE LATÉRALE ---
menu = st.sidebar.selectbox("Menu", ["Consulter le Planning", "Statistiques Heures 📊", "Administration 🔐"])

# --- 1. VUE CONSULTATION ---
if menu == "Consulter le Planning":
    st.subheader("🗓️ Séances programmées")
    if df.empty:
        st.info("Le planning est vide.")
    else:
        df_sorted = df.sort_values(by='Date_DT', ascending=True)
        for _, row in df_sorted.iterrows():
            d_fmt = row['Date_DT'].strftime('%d/%m/%Y') if pd.notnull(row['Date_DT']) else str(row['Date'])
            with st.expander(f"📅 {d_fmt} — {row['Equipage']}"):
                st.write(f"**⏰ Horaire :** {row['Horaire']} ({row['Heures']}h)")
                st.write(f"**🖥️ Simulateur :** {row['Simu']}")

# --- 2. VUE STATISTIQUES ---
elif menu == "Statistiques Heures 📊":
    st.subheader("📈 Bilan des heures par équipage")
    if df.empty:
        st.info("Aucune donnée disponible.")
    else:
        annees_dispo = sorted(df[df['Annee'] > 0]['Annee'].unique(), reverse=True)
        annee_sel = st.selectbox("Filtrer par année", ["Toutes"] + list(annees_dispo))
        
        df_stats = df.copy()
        if annee_sel != "Toutes":
            df_stats = df_stats[df_stats['Annee'] == annee_sel]

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Heures", f"{round(df_stats['Heures'].sum(), 1)} h")
        c2.metric("Séances", len(df_stats))
        c3.metric("Équipages", df_stats['Equipage'].nunique())

        st.divider()
        st.write("### Récapitulatif Annuel des Heures")
        df_valid = df[df['Annee'] > 0]
        if not df_valid.empty:
            pivot_h = df_valid.pivot_table(index='Equipage', columns='Annee', values='Heures', aggfunc='sum', fill_value=0)
            pivot_h['Total Cumulé'] = pivot_h.sum(axis=1)
            st.dataframe(pivot_h.sort_values(by='Total Cumulé', ascending=False), use_container_width=True)
            st.bar_chart(df_stats.groupby('Equipage')['Heures'].sum())

# --- 3. VUE ADMINISTRATION ---
elif menu == "Administration 🔐":
    pwd = st.sidebar.text_input("Code Admin", type="password")
    if pwd == "1234":
        tab1, tab2, tab3 = st.tabs(["➕ Ajouter", "📝 Modifier", "🗑️ Supprimer"])

        with tab1:
            with st.form("add_form", clear_on_submit=True):
                d = st.date_input("Date")
                e = st.text_input("Equipage")
                h = st.text_input("Horaire (ex: 13h30 - 17h00)")
                s = st.selectbox("Simu", ["SIM 1", "SIM 2", "SIM 3"])
                if st.form_submit_button("Valider l'ajout"):
                    payload = {"action": "add", "date": str(d), "equipage": e, "horaire": h, "simu": s}
                    requests.post(SCRIPT_URL, data=json.dumps(payload))
                    st.success("✅ Séance ajoutée !")
                    st.cache_data.clear()

        with tab2:
            if not df.empty:
                df['label_edit'] = df['Date'].astype(str) + " | " + df['Equipage'].astype(str) + " (" + df['Horaire'].astype(str) + ")"
                choix = st.selectbox("Modifier une séance", options=df['label_edit'].tolist())
                idx = df[df['label_edit'] == choix].index[0]
                row_sel = df.loc[idx]
                with st.form("edit_form"):
                    new_d = st.date_input("Date", value=pd.to_datetime(row_sel['Date']))
                    new_e = st.text_input("Equipage", value=row_sel['Equipage'])
                    new_h = st.text_input("Horaire", value=row_sel['Horaire'])
                    simu_list = ["SIM 1", "SIM 2", "SIM 3"]
                    cur_idx = simu_list.index(row_sel['Simu']) if row_sel['Simu'] in simu_list else 0
                    new_s = st.selectbox("Simu", simu_list, index=cur_idx)
                    if st.form_submit_button("Enregistrer"):
                        payload = {"action": "edit", "row_index": int(idx), "new_date": str(new_d), "new_equipage": new_e, "new_horaire": new_h, "new_simu": new_s}
                        requests.post(SCRIPT_URL, data=json.dumps(payload))
                        st.success("📝 Mis à jour !")
                        st.cache_data.clear()

        with tab3:
            if not df.empty:
                df['label_del'] = df['Date'].astype(str) + " | " + df['Equipage'].astype(str) + " (" + df['Horaire'].astype(str) + ")"
                choix_del = st.selectbox("Supprimer une séance", options=df['label_del'].tolist())
                idx_del = df[df['label_del'] == choix_del].index[0]
                st.warning("⚠️ Action définitive.")
                confirm = st.checkbox("Confirmer la suppression")
                if st.button("🗑️ Supprimer"):
                    if confirm:
                        payload = {"action": "delete", "row_index": int(idx_del)}
                        requests.post(SCRIPT_URL, data=json.dumps(payload))
                        st.success("Supprimé !")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
    else:
        st.info("Entrez le code administrateur.")
