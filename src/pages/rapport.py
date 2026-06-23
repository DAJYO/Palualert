"""Page « Rapport épidémique » : courbe des seuils et tableau par district/année."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src import config
from src.export_utils import exporter_png
from src.report_pdf import generer_pdf_rapport


def render(panel, P, epi, alerte):
    st.header("Rapport épidémique")

    districts = sorted(panel["district"].unique())
    col1, col2 = st.columns(2)
    d_sel = col1.selectbox("Choisir un district pour le rapport", districts)
    annee = col2.selectbox("Année", [2024, 2025, 2026])

    s = (
        P[(P["district"] == d_sel) & (P["date"].dt.year == annee)]
        .sort_values("date")
        .copy()
    )
    s["seuil_alerte"] = s["mois"].map(lambda m: alerte.get((d_sel, m), np.nan))
    s["seuil_epi"] = s["mois"].map(lambda m: epi.get((d_sel, m), np.nan))

    st.subheader(f"Courbe évolutive des prévisions épidémiques — {d_sel} ({annee})")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=s["mois"], y=s["seuil_epi"], mode="lines",
            line=dict(color="#d62728"), name="Seuil épidémique",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=s["mois"], y=s["seuil_alerte"], mode="lines",
            line=dict(color="#6a3d9a"), name="Seuil d'alerte",
            fill="tonexty", fillcolor="rgba(150,120,200,0.25)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=s["mois"], y=s["pred_cas"], mode="lines+markers",
            line=dict(color="#2ca02c", width=3), name="Prédiction",
        )
    )
    fig.update_layout(
        height=430,
        xaxis_title=f"Mois de l'année {annee}",
        yaxis_title="Nombre de cas",
    )
    if annee == config.ANNEE_PROJECTION:
        # Année entièrement projetée (au-delà des données observées)
        fig.add_vrect(
            x0=0.5, x1=12.5, fillcolor="#ff7f0e", opacity=0.08, line_width=0,
            annotation_text="Année projetée (climat = normales saisonnières)",
            annotation_position="top left",
            annotation_font=dict(size=11, color="#b35900"),
        )
    st.plotly_chart(fig, width='stretch')

    exporter_png(fig, f"rapport_{d_sel}_{annee}.png", cle="rapport")

    st.subheader("Tableau épidémique")
    tab = s[["mois", "pred_cas", "seuil_alerte", "seuil_epi", "niveau"]].copy()
    tab.columns = ["Mois", "Prédiction", "Seuil d'alerte", "Seuil épidémique", "Niveau"]
    st.dataframe(tab, width='stretch', hide_index=True)

    # --- Synthèse + export PDF ---
    vc = s["niveau"].value_counts()
    pred = s["pred_cas"].dropna()
    if not pred.empty:
        mois_pic = int(s.loc[pred.idxmax(), "mois"])
        pic = f"{pred.max():.0f} cas (mois {mois_pic})"
        total = f"{pred.sum():.0f} cas"
    else:
        pic = total = "—"
    resume = [
        ("Mois en épidémie", int(vc.get("Épidémie", 0))),
        ("Mois en alerte", int(vc.get("Alerte", 0))),
        ("Mois normaux", int(vc.get("Normal", 0))),
        ("Pic prévisionnel", pic),
        ("Total cas prévus (année)", total),
    ]

    with st.expander("📄 Exporter le rapport (PDF)"):
        if st.button("Générer le PDF", key="gen_pdf_rapport"):
            with st.spinner("Génération du PDF…"):
                pdf = generer_pdf_rapport(d_sel, annee, fig, tab, resume)
            st.download_button(
                "⬇️ Télécharger le rapport PDF",
                data=pdf,
                file_name=f"rapport_{d_sel}_{annee}.pdf".replace(" ", "_"),
                mime="application/pdf",
                key="dl_pdf_rapport",
            )
