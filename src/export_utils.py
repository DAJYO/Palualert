"""Utilitaire d'export d'une figure Plotly en image PNG (via kaleido)."""

import streamlit as st


def exporter_png(fig, nom_fichier, cle, label="📷 Exporter en image (PNG)",
                 width=1100, height=750, scale=2):
    """Affiche un bouton qui génère puis propose au téléchargement un PNG.

    La génération (coûteuse) n'a lieu qu'au clic, pas à chaque interaction.
    En cas d'absence de `kaleido`/Chrome, un message clair est affiché.
    """
    with st.expander(label):
        if st.button("Générer le PNG", key=f"gen_{cle}"):
            with st.spinner("Génération de l'image…"):
                try:
                    png = fig.to_image(
                        format="png", width=width, height=height, scale=scale
                    )
                except Exception as exc:  # kaleido/chrome absent ou erreur de rendu
                    st.error(
                        "Export PNG indisponible. Installez `kaleido` "
                        "(`pip install kaleido`) et, si besoin, un navigateur "
                        f"Chrome. Détail : {type(exc).__name__}"
                    )
                    return
            st.download_button(
                "⬇️ Télécharger l'image",
                data=png,
                file_name=nom_fichier,
                mime="image/png",
                key=f"dl_{cle}",
            )
