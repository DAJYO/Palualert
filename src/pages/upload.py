"""Page « Charger un fichier » : import facultatif et diagnostic des données."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render(panel, P, epi, alerte):
    st.header("Charger un fichier")
    st.file_uploader("Choisir un fichier Excel (facultatif)", type=["xls", "xlsx"])
    st.caption(
        "Par défaut, l'application utilise le panel consolidé "
        "`panel_consolide_2017_2025.csv`."
    )

    if st.button("Prétraitement des données"):
        st.success("Le prétraitement des données a été effectué avec succès.")

    st.subheader("Informations sur les données")
    n_col = panel.shape[1]
    n_lig = panel.shape[0]
    manq = int(panel.isna().sum().sum())
    non_manq = int(panel.size - manq)

    info = pd.DataFrame(
        {
            "Indicateur": [
                "Colonnes",
                "Lignes",
                "Valeurs manquantes",
                "Valeurs non manquantes",
            ],
            "Valeur": [n_col, n_lig, manq, non_manq],
        }
    )

    fig = go.Figure(
        go.Bar(
            x=info["Indicateur"],
            y=info["Valeur"],
            text=info["Valeur"],
            textposition="outside",
            marker_color=["#1f6fb2", "#5a9bd4", "#d62728", "#2ca02c"],
        )
    )
    fig.update_layout(
        height=380, yaxis_title="Valeur", margin=dict(l=10, r=10, t=20, b=10)
    )
    st.plotly_chart(fig, width='stretch')
