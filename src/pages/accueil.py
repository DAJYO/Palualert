"""Page d'accueil : présentation et indicateurs clés."""

import streamlit as st

from src import config


def render(panel, P, epi, alerte):
    st.header("Bienvenue")
    st.write(
        "Bienvenue sur l'application de surveillance du paludisme de la région "
        "de l'Extrême-Nord. Utilisez les onglets à gauche pour explorer les "
        "données, prévoir les cas et l'humidité, et générer le rapport "
        "épidémique par district."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Districts suivis", panel["district"].nunique())
    c1.metric("Période", config.PERIODE)
    c2.metric("Observations", f"{len(panel):,}".replace(",", " "))
    c2.metric("Modèle des cas (R²)", config.R2_CAS)
    c3.metric("Modèle d'humidité (R²)", config.R2_HUMIDITE)
    c3.metric("Horizon d'alerte", config.HORIZON_ALERTE)

    if config.GEOJSON_PATH.exists():
        st.success(
            f"🗺️ Carte choroplèthe des {config.NB_DISTRICTS_THEORIQUE} districts "
            "active — voir l'onglet **Carte des risques**."
        )
    else:
        st.info(
            f"ℹ️ La carte choroplèthe des {config.NB_DISTRICTS_THEORIQUE} districts "
            f"s'activera dès qu'un fichier GeoJSON des limites de district sera "
            f"déposé dans `{config.GEOJSON_PATH.name}` (voir `data/README.md`)."
        )
