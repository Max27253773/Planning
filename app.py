elif menu == "Administration 🔐":
    pwd = st.sidebar.text_input("Code Admin", type="password")
    if pwd == "1234":
        st.subheader("🛠️ Ajouter une séance")
        
        # Le formulaire commence ici
        with st.form("mon_formulaire", clear_on_submit=True):
            d = st.date_input("Date de la séance")
            e = st.text_input("Noms de l'équipage")
            h = st.text_input("Créneau horaire (ex: 08:30 - 12:30)")
            s = st.selectbox("Choisir le Simulateur", ["SIM 1", "SIM 2", "SIM 3"])
            
            # C'est cette ligne qui doit être BIEN ALIGNÉE (indentée) sous le "with"
            bouton_valider = st.form_submit_button("Enregistrer le planning")
            
            if bouton_valider:
                if e and h:
                    payload = {
                        "action": "add",
                        "date": str(d),
                        "equipage": e,
                        "horaire": h,
                        "simu": s
                    }
                    try:
                        r = requests.post(SCRIPT_URL, json=payload)
                        st.success("✅ Séance envoyée ! Elle apparaîtra dans quelques secondes.")
                        st.cache_data.clear() 
                    except:
                        st.error("Erreur de connexion au serveur Google.")
                else:
                    st.warning("Veuillez remplir les noms et l'horaire.")
    else:
        st.info("Veuillez saisir le code dans la barre latérale.")
