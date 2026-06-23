"""Page « Carte des risques » : choroplèthe des 33 districts.

Affiche, pour un mois donné, le niveau de risque (ou une variable au choix)
par district sur un fond de carte. Si le GeoJSON des limites de district est
absent, un repli (classement en barres) est proposé avec des instructions.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import config
from src.data_loader import apparier_districts, charger_geojson
from src.export_utils import exporter_png

MOIS_FR = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
    7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre",
    12: "Décembre",
}

# Libellé affiché -> (colonne du panel enrichi, est_categorie)
METRIQUES = {
    "Niveau de risque": ("niveau", True),
    "Cas prévus": ("pred_cas", False),
    "Cas observés": ("cas", False),
    "Humidité prévue (%)": ("pred_hum", False),
}

ORDRE_NIVEAUX = ["Normal", "Alerte", "Épidémie", "—"]
COULEURS_NIVEAUX = {
    "Normal": config.COULEUR_NORMAL,
    "Alerte": config.COULEUR_ALERTE,
    "Épidémie": config.COULEUR_EPIDEMIE,
    "—": config.COULEUR_INCONNU,
}


def _selecteurs(P):
    """Affiche les sélecteurs et retourne (annee, mois, libelle_metrique)."""
    annees = sorted(P["date"].dt.year.unique())
    c1, c2, c3 = st.columns(3)
    annee = c1.selectbox("Année", annees, index=len(annees) - 1)
    mois = c2.selectbox(
        "Mois", list(MOIS_FR.keys()), index=0, format_func=lambda m: MOIS_FR[m]
    )
    metrique = c3.selectbox("Variable cartographiée", list(METRIQUES.keys()))
    return annee, mois, metrique


def _instantane(P, annee, mois, colonne):
    """Une ligne par district pour le mois choisi (valeur de la colonne)."""
    sel = P[(P["date"].dt.year == annee) & (P["mois"] == mois)]
    return sel[["district", colonne]].drop_duplicates("district")


def _repli_barres(snap, colonne, est_cat, titre):
    """Repli sans GeoJSON : classement des districts en barres."""
    st.warning(
        "🗺️ Fichier GeoJSON absent — la carte est remplacée par un classement.\n\n"
        f"Déposez les limites des districts dans `{config.GEOJSON_PATH}` "
        "pour activer la carte choroplèthe (voir `data/README.md`)."
    )
    d = snap.dropna(subset=[colonne])
    if est_cat:
        d = d.assign(_o=d[colonne].map({n: i for i, n in enumerate(ORDRE_NIVEAUX)}))
        d = d.sort_values("_o", ascending=False)
        couleurs = d[colonne].map(COULEURS_NIVEAUX)
    else:
        d = d.sort_values(colonne, ascending=True)
        couleurs = config.COULEUR_EPIDEMIE
    fig = go.Figure(
        go.Bar(x=d[colonne], y=d["district"], orientation="h", marker_color=couleurs)
    )
    fig.update_layout(height=max(420, 18 * len(d)), title=titre, xaxis_title=titre)
    st.plotly_chart(fig, width="stretch")


def _carte(geojson, cle, snap, colonne, est_cat, titre, metrique, sous_titre=None):
    """Carte choroplèthe Plotly (maplibre, sans jeton) avec légende et notes."""
    commun = dict(
        geojson=geojson,
        locations="geo_id",
        featureidkey=f"properties.{cle}",
        center=config.CARTE_CENTRE,
        zoom=config.CARTE_ZOOM,
        map_style=config.CARTE_STYLE,
        hover_name="district",
        opacity=0.75,
    )
    if est_cat:
        fig = px.choropleth_map(
            snap, color=colonne,
            category_orders={colonne: ORDRE_NIVEAUX},
            color_discrete_map=COULEURS_NIVEAUX,
            **commun,
        )
    else:
        fig = px.choropleth_map(
            snap, color=colonne,
            color_continuous_scale="YlOrRd",
            **commun,
        )
        fig.update_coloraxes(colorbar_title_text=metrique)

    # Titre + sous-titre (synthèse)
    texte_titre = titre if not sous_titre else f"{titre}<br><sup>{sous_titre}</sup>"

    fig.update_layout(
        height=580,
        margin=dict(l=0, r=0, t=70, b=10),
        title=dict(text=texte_titre, x=0.01, xanchor="left"),
        # Légende encadrée et lisible (variables catégorielles)
        legend=dict(
            title_text="Niveau de risque",
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#cccccc",
            borderwidth=1,
            x=0.01, y=0.99, xanchor="left", yanchor="top",
        ),
    )

    # Annotation de source / attribution (bas de carte)
    fig.add_annotation(
        text="Source : geoBoundaries (ADM3) · Prototype ENSPM Maroua",
        xref="paper", yref="paper", x=0.99, y=0.01,
        xanchor="right", yanchor="bottom", showarrow=False,
        font=dict(size=10, color="#555"),
        bgcolor="rgba(255,255,255,0.6)",
    )
    return fig


def _ajouter_points(fig, points, colonne, est_cat, vmin, vmax):
    """Ajoute des marqueurs pour les districts sans polygone (ex. Mada)."""
    if points.empty:
        return
    if est_cat:
        marker = dict(size=15, color=points[colonne].map(COULEURS_NIVEAUX),
                      symbol="circle")
    else:
        marker = dict(size=15, color=points[colonne], colorscale="YlOrRd",
                      cmin=vmin, cmax=vmax, showscale=False, symbol="circle")
    fig.add_trace(
        go.Scattermap(
            lat=points["lat"], lon=points["lon"],
            mode="markers+text", marker=marker,
            text=points["district"], textposition="top center",
            name="Localité (sans polygone)",
            hovertext=[f"{d} — {v}" for d, v in zip(points["district"], points[colonne])],
            hoverinfo="text",
        )
    )


def render(panel, P, epi, alerte):
    st.header("Carte des risques par district")

    annee, mois, metrique = _selecteurs(P)
    colonne, est_cat = METRIQUES[metrique]
    titre = f"{metrique} — {MOIS_FR[mois]} {annee}"

    snap = _instantane(P, annee, mois, colonne)
    if snap[colonne].dropna().empty:
        st.info(f"Aucune donnée disponible pour {MOIS_FR[mois]} {annee}.")
        return

    geojson = charger_geojson()
    if geojson is None:
        _repli_barres(snap, colonne, est_cat, titre)
        return

    # Appariement des noms de district avec le GeoJSON
    districts = panel["district"].unique()
    cle, correspondance = apparier_districts(geojson, districts)
    if cle is None:
        st.error(
            "Le GeoJSON ne contient aucune propriété correspondant aux noms de "
            "district du panel. Vérifiez le fichier (voir `data/README.md`)."
        )
        _repli_barres(snap, colonne, est_cat, titre)
        return

    snap = snap.copy()
    snap["geo_id"] = snap["district"].map(correspondance)

    # Districts sans polygone, représentés par un marqueur (ex. Mada)
    points = snap[snap["district"].isin(config.DISTRICTS_POINTS)].dropna(
        subset=[colonne]
    ).copy()
    points["lat"] = points["district"].map(lambda d: config.DISTRICTS_POINTS[d]["lat"])
    points["lon"] = points["district"].map(lambda d: config.DISTRICTS_POINTS[d]["lon"])

    matched = snap.dropna(subset=["geo_id"])
    non_localises = sorted(
        snap.loc[
            snap["geo_id"].isna() & ~snap["district"].isin(config.DISTRICTS_POINTS),
            "district",
        ]
    )

    # Synthèse (sous-titre de la carte) sur l'ensemble des districts localisés
    localises = snap[snap["geo_id"].notna() | snap["district"].isin(config.DISTRICTS_POINTS)]
    if est_cat:
        vc = localises[colonne].value_counts()
        sous_titre = " · ".join(
            f"{n} : {int(vc[n])}" for n in ORDRE_NIVEAUX if vc.get(n, 0)
        )
    else:
        vals_all = localises[colonne].dropna()
        sous_titre = (
            f"min {vals_all.min():.0f} · moy {vals_all.mean():.0f} · "
            f"max {vals_all.max():.0f}"
            if not vals_all.empty else None
        )

    fig = _carte(geojson, cle, matched, colonne, est_cat, titre, metrique, sous_titre)
    vmin = vmax = None
    if not est_cat:
        vals = snap[colonne].dropna()
        if not vals.empty:
            vmin, vmax = float(vals.min()), float(vals.max())
    _ajouter_points(fig, points, colonne, est_cat, vmin, vmax)
    st.plotly_chart(fig, width="stretch")

    exporter_png(fig, f"carte_{annee}_{mois:02d}.png", cle="carte")

    st.caption(
        f"Propriété GeoJSON : `{cle}` · {len(matched)} districts en polygone · "
        f"{len(points)} en marqueur · "
        f"{len(districts) - len(non_localises)}/{len(districts)} localisés."
    )
    if non_localises:
        st.warning(
            "Districts non localisés (ni polygone ni coordonnées) : "
            + ", ".join(non_localises)
        )
