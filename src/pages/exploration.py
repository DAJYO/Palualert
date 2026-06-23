"""Page « Exploration des données » : tableau pivot et séries temporelles."""

import plotly.graph_objects as go
import streamlit as st

from src import config


def render(panel, P, epi, alerte):
    st.header("Visualisation des données")

    districts = sorted(panel["district"].unique())

    # --- Visualisation numérique (tableau large : date x districts) ---
    table = panel.pivot(index="date", columns="district", values="cas")
    n = st.number_input("Nombre de lignes à afficher", 5, len(table), 10)
    st.dataframe(table.tail(int(n)), width='stretch')

    st.divider()

    # --- Visualisation graphique (courbe d'une variable) ---
    st.subheader("Visualisation graphique")
    col1, col2 = st.columns(2)
    d_sel = col1.selectbox("Choisir un district", districts)
    v_sel = col2.selectbox("Choisir une variable", config.VARIABLES_EXPLORABLES)

    s = panel[panel["district"] == d_sel].sort_values("date")
    fig = go.Figure(
        go.Scatter(x=s["date"], y=s[v_sel], mode="lines", line=dict(color="#222"))
    )
    fig.update_layout(
        height=420,
        title=f"Série temporelle — {v_sel} ({d_sel})",
        xaxis_title="date",
        yaxis_title=v_sel,
    )
    st.plotly_chart(fig, width='stretch')
