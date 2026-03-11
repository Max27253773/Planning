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
        return data
    except:
        return pd.DataFrame(columns=["Date", "Equipage", "Horaire", "Simu"])

df = load_data()

menu = st.sidebar.selectbox("Menu", ["Consulter le Planning", "Administration 🔐"])

if menu == "Consulter le Planning":
    st.subheader("🗓️ Séances programmées")
    if df.empty or len(df.columns) < 2:
        st.info("Le planning est vide.")
    else:
        df_sorted = df.sort_values(by='Date_DT', ascending=True)
        for _, row in df_sorted.iterrows():
            try:
                d_fmt = row['Date_DT'].strftime('%d/%m/%Y')
            except:
                d_fmt = str(row['Date'])
            
            with st.expander(f"📅 {d_fmt} — {row['Equipage']}"):
                st.write(f"**⏰ Horaire :** {row['Horaire']}")
                st.write(f"**🖥️ Simulateur :** {row['Simu']}")

elif menu == "Administration 🔐":
    pwd = st.sidebar.text_input("Code Admin", type="password")
    if pwd == "1234":
        tab1, tab2, tab3 = st.tabs(["➕ Ajouter", "📝 Modifier", "🗑️ Supprimer"])

        with tab1:
            with st.form("add_form", clear_on_submit=True):
                d = st.date_input("Date")
                e = st.text_input("Equipage")
                h = st.text_input("Horaire (ex: 08h-12h)")
                s = st.selectbox("Simu", ["SIM 1", "SIM 2", "SIM 3"])
                if st.form_submit_button("Valider l'ajout"):
                    payload = {"action": "add", "date": str(d), "equipage": e, "horaire": h, "simu": s}
                    requests.post(SCRIPT_URL, data=json.dumps(payload))
                    st.success("✅ Séance ajoutée !")
                    st.cache_data.clear()

        # --- ONGLET MODIFIER (Détails enrichis) ---
        with tab2:
            if not df.empty:
                # Label enrichi : Date - Equipage - Horaire - Simu
                df['label_edit'] = df['Date'].astype(str) + " | " + df['Equipage'].astype(str) + " | " + df['Horaire'].astype(str) + " (" + df['Simu'].astype(str) + ")"
                choix = st.selectbox("Sélectionner la séance à modifier", options=df['label_edit'].tolist())
                idx = df[df['label_edit'] == choix].index[0]
                row_sel = df.loc[idx]

                with st.form("edit_form"):
                    new_d = st.date_input("Nouvelle Date", value=pd.to_datetime(row_sel['Date']))
                    new_e = st.text_input("Nouvel Equipage", value=row_sel['Equipage'])
                    new_h = st.text_input("Nouvel Horaire", value=row_sel['Horaire'])
                    new_s = st.selectbox("Nouveau Simu", ["SIM 1", "SIM 2", "SIM 3"], 
                                       index=["SIM 1", "SIM 2", "SIM 3"].index(row_sel['Simu']) if row_sel['Simu'] in ["SIM 1", "SIM 2", "SIM 3"] else 0)
                    if st.form_submit_button("Mettre à jour"):
                        payload = {
                            "action": "edit", "row_index": int(idx),
                            "new_date": str(new_d), "new_equipage": new_e, 
                            "new_horaire": new_h, "new_simu": new_s
                        }
                        requests.post(SCRIPT_URL, data=json.dumps(payload))
                        st.success("📝 Mise à jour réussie !")
                        st.cache_data.clear()

        # --- ONGLET SUPPRIMER (Sécurité + Détails enrichis) ---
        with tab3:
            if not df.empty:
                # Label enrichi pour la suppression
                df['label_del'] = df['Date'].astype(str) + " | " + df['Equipage'].astype(str) + " | " + df['Horaire'].astype(str) + " (" + df['Simu'].astype(str) + ")"
                choix_del = st.selectbox("Sélectionner la séance à supprimer", options=df['label_del'].tolist())
                idx_del = df[df['label_del'] == choix_del].index[0]
                
                st.warning("⚠️ Attention : la suppression est définitive.")
                confirm = st.checkbox("Je confirme vouloir supprimer cette séance précise")
                
                if st.button("🗑️ Supprimer définitivement"):
                    if confirm:
                        payload = {"action": "delete", "row_index": int(idx_del)}
                        requests.post(SCRIPT_URL, data=json.dumps(payload))
                        st.success(f"Séance supprimée avec succès.")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Veuillez cocher la case de confirmation avant de cliquer sur supprimer.")
    else:
        st.info("Entrez le code admin.")
