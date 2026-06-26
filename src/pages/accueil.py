"""Page d'accueil : carte du risque courant et résumé compréhensible."""

import streamlit as st

from src import config
from src.pages.carte import MOIS_FR, carte_risque_courante


def render(panel, P, epi, alerte):
    st.header("Bienvenue")
    st.write(
        "Application de surveillance du paludisme de la région de l'Extrême-Nord. "
        "La carte ci-dessous montre, pour chaque district, le niveau de risque "
        "prévu. Utilisez les onglets à gauche pour le détail par district."
    )

    fig, annee, mois, comptes = carte_risque_courante(panel, P)

    if fig is not None:
        st.subheader(f"Niveau de risque par district — {MOIS_FR[mois]} {annee}")
        st.plotly_chart(fig, width="stretch")

        # Résumé simple, lisible par tout personnel
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Districts suivis", panel["district"].nunique())
        c2.metric("🟢 Normal", int(comptes.get("Normal", 0)))
        c3.metric("🟠 En alerte", int(comptes.get("Alerte", 0)))
        c4.metric("🔴 En épidémie", int(comptes.get("Épidémie", 0)))

        st.caption(
            "Lecture : 🟢 **vert** = situation normale · 🟠 **orange** = alerte "
            "(à surveiller) · 🔴 **rouge** = risque d'épidémie (à intervenir). "
            "Le point isolé correspond au district de Mada. "
            "Carte **prévisionnelle** : voir l'onglet *Rapport épidémique* pour le détail."
        )
    else:
        # Repli si le fond de carte n'est pas disponible
        st.info(
            f"ℹ️ La carte des {config.NB_DISTRICTS_THEORIQUE} districts s'activera "
            f"dès qu'un fichier GeoJSON sera déposé dans `{config.GEOJSON_PATH.name}` "
            "(voir `data/README.md`)."
        )
        c1, c2 = st.columns(2)
        c1.metric("Districts suivis", panel["district"].nunique())
        c2.metric("Période des données", config.PERIODE)
