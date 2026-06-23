"""Page « Prévisions » : prévision des cas et de l'humidité par district."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import config


def _bande_projection(fig, debut, fin):
    """Ombre la période projetée (≥ `debut`) et trace la séparation.

    Les dates sont passées en chaîne ISO : un objet pandas Timestamp dans une
    forme/annotation rendrait la figure non sérialisable (échec de l'export
    PNG/PDF via kaleido).
    """
    debut_s = debut.strftime("%Y-%m-%d")
    fin_s = fin.strftime("%Y-%m-%d")
    fig.add_vrect(
        x0=debut_s, x1=fin_s, fillcolor="#ff7f0e", opacity=0.10, line_width=0,
        annotation_text=f"Projection {config.ANNEE_PROJECTION}",
        annotation_position="top left",
        annotation_font=dict(size=11, color="#b35900"),
    )
    fig.add_vline(x=debut_s, line_dash="dash", line_color="#888")


def render(panel, P, epi, alerte):
    st.header("Prévisions")

    districts = sorted(panel["district"].unique())
    col1, col2 = st.columns(2)
    d_sel = col1.selectbox("Choisir un district", districts)
    col2.select_slider("Horizon d'alerte (mois)", options=[1, 2, 3], value=2)

    s = P[P["district"] == d_sel].sort_values("date")

    # Bornes de la zone projetée (à partir du 1er janvier de l'année projetée)
    debut_proj = pd.Timestamp(f"{config.ANNEE_PROJECTION}-01-01")
    fin_serie = s["date"].max()
    montrer_proj = fin_serie >= debut_proj

    # --- Prévision des cas ---
    st.subheader("Prévision des cas")
    fig1 = go.Figure()
    fig1.add_trace(
        go.Scatter(
            x=s["date"], y=s["cas"], name="Données d'origine",
            mode="lines", line=dict(color="#6a3d9a"),
        )
    )
    fig1.add_trace(
        go.Scatter(
            x=s["date"], y=s["pred_cas"], name="Prévisions",
            mode="lines", line=dict(color="#e31a1c"),
        )
    )
    fig1.update_layout(height=380, xaxis_title="Date", yaxis_title="Cas")
    if montrer_proj:
        _bande_projection(fig1, debut_proj, fin_serie)
    st.plotly_chart(fig1, width='stretch')

    # --- Prévision de l'humidité ---
    st.subheader("Prévision de l'humidité (signal annonciateur)")
    fig2 = go.Figure()
    fig2.add_trace(
        go.Scatter(
            x=s["date"], y=s["humidite"], name="Observée",
            mode="lines", line=dict(color="#333"),
        )
    )
    fig2.add_trace(
        go.Scatter(
            x=s["date"], y=s["pred_hum"], name="Prévue",
            mode="lines", line=dict(color="#1f6fb2", dash="dash"),
        )
    )
    fig2.update_layout(height=320, xaxis_title="Date", yaxis_title="Humidité (%)")
    if montrer_proj:
        _bande_projection(fig2, debut_proj, fin_serie)
    st.plotly_chart(fig2, width='stretch')

    # --- Tableau ---
    st.subheader("Tableau des prévisions")
    tab = s[["date", "pred_cas", "pred_hum", "niveau"]].dropna().copy()
    tab.columns = ["Date", "Cas prévus", "Humidité prévue (%)", "Niveau"]
    st.dataframe(tab.tail(24), width='stretch', hide_index=True)
