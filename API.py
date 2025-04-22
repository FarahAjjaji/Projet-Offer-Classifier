import streamlit as st
import os 
import datetime
import shutil
import pandas as pd
from streamlit_pdf_viewer import pdf_viewer
from main import main  # Importer la fonction main du module main_script2
import base64

TMP_DIR = "tmp"
# Fonction pour traiter un fichier PDF
def process_file(pdf_path):
    # Appeler la fonction principale pour traiter le fichier
    result = main(pdf_path)
    return result

def get_majors():
    csv_path = "majors_keywords.csv"
    if os.path.exists(csv_path):
        majors_df = pd.read_csv(csv_path)
        major_list = majors_df['Major'].dropna().unique().tolist()
    else:
        st.error(f"Le fichier {csv_path} est introuvable.")
        major_list = []
    return major_list

# Fonction pour afficher le dashboard
def dashboard():
    st.title("Dashboard")

    # Ajouter un uploader de fichiers
    uploaded_files = st.file_uploader("Déposez vos fichiers PDF ici", type=["pdf"], accept_multiple_files=True)

    # Traiter les fichiers téléchargés
    if uploaded_files:
        # Réinitialiser l'état de classification
        st.session_state.classified_files = {uploaded_file.name: False for uploaded_file in uploaded_files}  # Utiliser le nom du fichier

        # Initialiser la barre de progression
        progress_bar = st.progress(0)
        total_files = len(uploaded_files)

        results = {}
        for i, uploaded_file in enumerate(uploaded_files):
            if not os.path.exists(TMP_DIR):
                os.makedirs(TMP_DIR)
            # Sauvegarder le fichier dans le dossier "tmp"
            pdf_path = os.path.join(TMP_DIR, uploaded_file.name)
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Traiter le fichier PDF
            result = process_file(pdf_path)
            if result is not None:  # Vérifiez si le résultat n'est pas None
                result['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                results[uploaded_file.name] = result
            else:
                st.error(f"Erreur lors du traitement de {uploaded_file.name}. Veuillez vérifier le fichier.")

            # Mettre à jour la barre de progression
            progress_bar.progress((i + 1) / total_files)

        # Sauvegarder les résultats dans la session
        st.session_state.results = results

        st.write("Fin du traitement. Vous pouvez consulter les détails de chaque classement des offres.")

# Fonction pour gérer le déplacement ou la copie des fichiers
def handle_file_movement(pdf_file, result, classifications, keywords):
    old_pdf_path = os.path.join(TMP_DIR, pdf_file)
    for classification_name in classifications:
        classification_parts = classification_name.upper().split()

        # Trouver le mot-clé dans la classification
        for keyword in keywords:
            if keyword in classification_parts:
                keyword_index = classification_parts.index(keyword)
                classification_sub_name = "_".join(classification_parts[keyword_index + 1:])
                
                # Construire le chemin du répertoire
                directory_path = os.path.join(
                    "OFFRES",
                    result['type_contrat'].upper(),
                    *classification_parts[:keyword_index],
                    classification_parts[keyword_index],
                    classification_sub_name.upper()
                )
                os.makedirs(directory_path, exist_ok=True)

                # Déplacer ou copier le fichier
                final_path = os.path.join(directory_path, pdf_file)
                try:
                    shutil.copy2(old_pdf_path, final_path)
                    st.success(f"Le fichier {pdf_file} a été copié vers {final_path}")
                except Exception as e:
                    st.error(f"Erreur lors de la copie de {pdf_file} vers {final_path} : {e}")

# Fonction principale pour afficher les offres classées
def classified_offers():
    st.title("Offres Classées")

    st.write("Une fois vérifié, appuyez sur ce bouton pour envoyer ces offres dans les dossiers SharePoint.")
    if st.button("Envoyer à SharePoint"):
        st.info("Les offres ont été envoyées à SharePoint.")

    # Vérifier si les résultats sont disponibles
    if 'results' in st.session_state:
        results = st.session_state.results

        # Initialiser l'état de classification pour chaque fichier
        if 'classified_files' not in st.session_state:
            st.session_state.classified_files = {pdf_file: False for pdf_file in results.keys()}

        classifying_done = all(st.session_state.classified_files.values())
        keywords = ["MASTER", "BACHELOR", "MASTÈRE","MBA"]

        # Parcourir chaque fichier
        for pdf_file, result in results.items():
            col1, col2 = st.columns([1, 1])

            with col1:
                st.write(f"### {pdf_file}")
                if st.button(f"Changer type de contrat", key=f"toggle_{pdf_file}"):
                    result['type_contrat'] = "Alternance" if result['type_contrat'] == "Stage" else "Stage"
                st.write(f"Type de contrat: {result['type_contrat']}")
                st.write(f"Heure de traitement: {result['timestamp']}")
                st.write(f"Classification principale: {result['classification']}")
                st.write("Autres classifications disponibles:")

                # Stocker les classifications sélectionnées
                selected_classifications = []

                # Ajouter des checkboxes pour sélectionner les classifications
                if st.checkbox(f"Utiliser la classification principale : {result['classification']}", key=f"{pdf_file}_main"):
                    selected_classifications.append(result['classification'].upper())

                for classification in result['others']:
                    if st.checkbox(f"Utiliser l'autre classification : {classification}", key=f"{pdf_file}_{classification}"):
                        selected_classifications.append(classification.upper())
                # Ajouter une liste déroulante pour choisir une classification supplémentaire
                major_list = get_majors()
                selected_major = st.selectbox(
                    "Voir plus :", 
                    options=["Aucun"] + major_list, 
                    key=f"{pdf_file}_dropdown"
                )
                if selected_major != "Aucun":
                    selected_classifications.append(selected_major.upper())

                # Stocker les sélections dans la session
                st.session_state[f"{pdf_file}_selected_classifications"] = selected_classifications

            with col2:
                with st.expander(f"Voir le fichier PDF : {pdf_file}"):
                    pdf_path = os.path.join(TMP_DIR, pdf_file)
                    # Vérifier si le fichier existe
                    if os.path.exists(pdf_path):        
                        #pdf_viewer(pdf_path)
                        show_pdf(pdf_path)
                    else:
                        st.warning(f"Le fichier {pdf_path} n'existe pas.")


        # Bouton pour appliquer la classification par défaut de tous les fichiers 
        if st.button("Appliquer la classification par défaut") and not classifying_done:
            for pdf_file, result in results.items():
                classification_data = result['classification']
                classifications = (
                    [item.upper() for item in classification_data]
                    if isinstance(classification_data, list)
                    else [classification_data.upper()]
                )
                handle_file_movement(pdf_file, result, classifications, keywords)
            # Supprimer le dossier temporaire
            if os.path.exists(TMP_DIR):
                shutil.rmtree(TMP_DIR)
                st.info(f"Le dossier {TMP_DIR} a été supprimé.")
            st.session_state.classified_files = {pdf_file: True for pdf_file in results.keys()}

        # Bouton pour appliquer les classifications sélectionnées
        if 'processing_started' not in st.session_state:
            st.session_state.processing_started = False
        if 'proceed_confirmed' not in st.session_state:
            st.session_state.proceed_confirmed = False
        
        # Main processing button
        if st.button("Appliquer les classifications sélectionnées") and not classifying_done:
            st.session_state.processing_started = True
        
        if st.session_state.processing_started:
            files_without_class = [
                pdf_file for pdf_file, result in results.items() 
                if not st.session_state.get(f"{pdf_file}_selected_classifications", [])
            ]
            
            if files_without_class and not st.session_state.proceed_confirmed:
                files_list = "\n".join([f"- {f}" for f in files_without_class])
                st.warning(f"Les fichiers suivants n'ont pas de classification:\n{files_list}")
                if st.button("Continuer quand même?"):
                    st.session_state.proceed_confirmed = True
                    st.rerun()
            
            elif not files_without_class or st.session_state.proceed_confirmed:
                # Process files
                for pdf_file, result in results.items():
                    selected_classifications = st.session_state.get(f"{pdf_file}_selected_classifications", [])
                    if not selected_classifications:
                        st.warning(f"Aucune classification sélectionnée pour {pdf_file}.")
                        continue
                    handle_file_movement(pdf_file, result, selected_classifications, keywords)
                
                # Cleanup
                if os.path.exists("tmp"):
                    shutil.rmtree("tmp")
                    st.info("Le dossier 'tmp' a été supprimé.")
                
                st.session_state.classified_files = {pdf_file: True for pdf_file in results.keys()}
    else:
        st.write("Aucune offre classée pour le moment. Veuillez traiter les fichiers depuis le dashboard.")

def show_pdf(file_path):
    with open(file_path,"rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# Interface utilisateur Streamlit
st.sidebar.title("Navigation")
page = st.sidebar.radio("Aller à", ["Dashboard", "Offres Classées"])

if page == "Dashboard":
    dashboard()
elif page == "Offres Classées":
    classified_offers()
