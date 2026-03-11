import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Planning Simu", layout="wide")
st.title("✈️ Planning Équipages")

# Connexion au Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

# Lecture des données (on force le rafraîchissement à chaque action)
df = conn.read(ttl=0) 

menu = st.sidebar.selectbox("Menu", ["Consulter le Planning", "Administration 🔐"])

if menu == "Consulter le Planning":
    if df is None or df.empty:
        st.info("Aucun vol prévu.")
    else:
        # Tri par date
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df_view = df.sort_values(by="Date")
        
        for _, row in df_view.iterrows():
            date_str = row['Date'].strftime('%d/%m/%Y') if not pd.isnull(row['Date']) else "Date inconnue"
            with st.expander(f"📅 {date_str} - {row['Equipage']}"):
                st.write(f"**Horaire :** {row['Horaire']}")
                st.write(f"**Appareil :** {row['Simu']}")

elif menu == "Administration 🔐":
    pwd = st.sidebar.text_input("Code Admin", type="password")
    if pwd == "1234":
        st.subheader("🛠️ Gestion du Planning")
        
        # --- AJOUT ---
        with st.form("add_form", clear_on_submit=True):
            st.write("### Ajouter une séance")
            d = st.date_input("Date")
            e = st.text_input("Equipage")
            h = st.text_input("Horaire (ex: 08h-12h)")
            s = st.selectbox("Simu", ["SIM 1", "SIM 2", "SIM 3"])
            
            if st.form_submit_button("Enregistrer"):
                new_row = pd.DataFrame([{"Date": str(d), "Equipage": e, "Horaire": h, "Simu": s}])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success("Planning mis à jour !")
                st.rerun()

        st.markdown("---")
        
        # --- SUPPRESSION ---
        st.write("### Supprimer une séance")
        if not df.empty:
            indices = df.index.tolist()
            # On crée une liste lisible pour choisir quoi supprimer
            options = [f"{df.loc[i, 'Date']} - {df.loc[i, 'Equipage']}" for i in indices]
            to_delete = st.selectbox("Sélectionner la séance à retirer :", options)
            
            if st.button("Supprimer définitivement"):
                index_to_drop = options.index(to_delete)
                df_dropped = df.drop(df.index[index_to_drop])
                conn.update(data=df_dropped)
                st.warning("Séance supprimée.")
                st.rerun()
    else:
        st.info("Entrez le code pour accéder aux modifications.")
