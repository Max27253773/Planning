import streamlit as st
import pandas as pd
import requests
import time
import json

# --- CONFIGURATION ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1mmPHzEY9p7ohdzvIYvwQOvqmKNa_8VQdZyl4sj1nksw/export?format=csv&gid=0"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxhetuY5QpJEvl-Wv1BMGej5FeW6S3-WDcbS1DwcwUVT-Yt3e8th1XG9pPCcbrwPu5ITw/exec"

st.set_page_config(page_title="Planning Simu Pro", layout="wide")
st.title("✈️ Planning Équipages")

@st.cache_data(ttl=2)
def load_data():
    try:
        url_force = f"{SHEET_CSV_URL}&v={time.time()}"
        data = pd.read_csv(url_force)
        data['Date_DT'] = pd.to_datetime(data['Date'], errors='coerce')
        # Extraction de l'année pour les stats
        data['Annee'] = data['Date_DT'].dt.year.fillna(0).astype(int)
        return data
    except:
        return pd.DataFrame(columns=["Date", "Equipage", "Horaire", "Simu", "Annee"])

df = load_data()

menu = st.sidebar.selectbox("Menu", ["Consulter le Planning", "Statistiques 📊", "Administration 🔐"])

# --- VUE UTILISATEUR ---
if menu == "Consulter le Planning":
    st.subheader("🗓️ Séances programmées")
    if df.empty or len(df.columns) < 2:
        st.info("Le planning est vide.")
    else:
        df_sorted = df.sort_values(by='Date_DT', ascending=True)
        for _, row in df_sorted.iterrows():
            d_fmt = row['Date_DT'].strftime('%d/%m/%Y') if pd.notnull(row['Date_DT']) else str(row['Date'])
            with st.expander(f"📅 {d_fmt} — {row['Equipage']}"):
                st.write(f"**⏰ Horaire :** {row['Horaire']} | **🖥️ Simu :** {row['Simu']}")

# --- VUE STATISTIQUES ---
elif menu == "Statistiques 📊":
    st.subheader("Analyse de l'activité")
    if df.empty:
        st.info("Aucune donnée disponible pour les statistiques.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            total_seances = len(df)
            st.metric("Total des séances", total_seances)
        
        with col2:
            equipages_uniques = df['Equipage'].nunique()
            st.metric("Nombre d'équipages", equipages_uniques)

        st.divider()

        # Graphique par équipage
        st.write("### Nombre de séances par équipage")
        stats_equipage = df['Equipage'].value_counts()
        st.bar_chart(stats_equipage)

        # Tableau détaillé par Année et Équipage
        st.write("### Récapitulatif par Année")
        # On filtre les années valides (supérieures à 0)
        df_valid_years = df[df['Annee'] > 0]
        if not df_valid_years.empty:
            pivot_table = df_valid_years.pivot_table(
                index='Equipage', 
                columns='Annee', 
                values='Date', 
                aggfunc='count', 
                fill_value=0
            )
            st.table(pivot_table)
        else:
            st.warning("Formats de date invalides pour le calcul par année.")

# --- VUE ADMIN ---
elif menu == "Administration 🔐":
    pwd = st.sidebar.text_input("Code Admin", type="password")
    if pwd == "1234":
        tab1, tab2, tab3 = st.tabs(["➕ Ajouter", "📝 Modifier", "🗑️ Supprimer"])

        with tab1:
            with st.form("add_form", clear_on_submit=True):
                d = st.date_input("Date")
                e = st.text_input("Equipage")
                h = st.text_input("Horaire")
                s = st.selectbox("Simu", ["SIM 1", "SIM 2", "SIM 3"])
                if st.form_submit_button("Valider"):
                    payload = {"action": "add", "date": str(d), "equipage": e, "horaire": h, "simu": s}
                    requests.post(SCRIPT_URL, data=json.dumps(payload))
                    st.success("Ajouté !")
                    st.cache_data.clear()

        with tab2:
            if not df.empty:
                df['label_edit'] = df['Date'].astype(str) + " | " + df['Equipage'].astype(str) + " | " + df['Horaire'].astype(str)
                choix = st.selectbox("Sélectionner la séance", options=df['label_edit'].tolist())
                idx = df[df['label_edit'] == choix].index[0]
                row_sel = df.loc[idx]
                with st.form("edit_form"):
                    new_d = st.date_input("Date", value=pd.to_datetime(row_sel['Date']))
                    new_e = st.text_input("Equipage", value=row_sel['Equipage'])
                    new_h = st.text_input("Horaire", value=row_sel['Horaire'])
                    new_s = st.selectbox("Simu", ["SIM 1", "SIM 2", "SIM 3"])
                    if st.form_submit_button("Mettre à jour"):
                        payload = {"action": "edit", "row_index": int(idx), "new_date": str(new_d), "new_equipage": new_e, "new_horaire": new_h, "new_simu": new_s}
                        requests.post(SCRIPT_URL, data=json.dumps(payload))
                        st.success("Modifié !")
                        st.cache_data.clear()

        with tab3:
            if not df.empty:
                df['label_del'] = df['Date'].astype(str) + " | " + df['Equipage'].astype(str) + " | " + df['Horaire'].astype(str)
                choix_del = st.selectbox("Séance à supprimer", options=df['label_del'].tolist())
                idx_del = df[df['label_del'] == choix_del].index[0]
                st.warning("⚠️ Suppression définitive.")
                confirm = st.checkbox("Confirmer la suppression")
                if st.button("🗑️ Supprimer"):
                    if confirm:
                        payload = {"action": "delete", "row_index": int(idx_del)}
                        requests.post(SCRIPT_URL, data=json.dumps(payload))
                        st.cache_data.clear()
                        st.rerun()
    else:
        st.info("Entrez le code admin.")
