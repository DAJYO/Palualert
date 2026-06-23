"""
Surveillance Palustre — Région de l'Extrême-Nord du Cameroun
============================================================

Application d'alerte précoce du paludisme reposant sur deux modèles Random
Forest (prévision des cas et de l'humidité), par district et au pas mensuel.

Onglets : Accueil | Charger un fichier | Exploration des données | Prévisions |
          Rapport épidémique

Lancement :
    pip install -r requirements.txt
    streamlit run app.py

Fichiers requis :
    data/panel_consolide_2017_2025.csv
    models/modele_final_random_forest.pkl
    models/modele_climat_humidite.pkl

Point d'entrée : ce fichier se contente de configurer la page, d'orchestrer
le chargement (via `pipeline.preparer`) et de router vers la page choisie.
Toute la logique métier vit dans le package `src/`.
"""

import streamlit as st

from src.pages import accueil, carte, exploration, previsions, rapport, upload
from src.pipeline import preparer

# ------------------------------------------------------------------ #
#  Configuration de la page
# ------------------------------------------------------------------ #
st.set_page_config(
    page_title="Surveillance Palustre — Extrême-Nord",
    page_icon="🦟",
    layout="wide",
)

# ------------------------------------------------------------------ #
#  Préparation des données (mise en cache dans le pipeline)
# ------------------------------------------------------------------ #
panel, P, epi, alerte = preparer()

# ------------------------------------------------------------------ #
#  Navigation (barre latérale)
# ------------------------------------------------------------------ #
PAGES = {
    "Accueil": accueil,
    "Charger un fichier": upload,
    "Exploration des données": exploration,
    "Carte des risques": carte,
    "Prévisions": previsions,
    "Rapport épidémique": rapport,
}

st.sidebar.title("🦟 Surveillance Palustre")
choix = st.sidebar.radio("Navigation", list(PAGES.keys()))
st.sidebar.caption("Région de l'Extrême-Nord — Cameroun")

# ------------------------------------------------------------------ #
#  Rendu de la page choisie
# ------------------------------------------------------------------ #
PAGES[choix].render(panel, P, epi, alerte)

st.sidebar.caption("Prototype — mémoire ENSPM Maroua")
