"""
Orchestration : assemblage des données, des modèles et des seuils.

`preparer()` produit l'objet central de l'application :
  - `panel`  : données brutes nettoyées ;
  - `P`      : panel enrichi des prévisions (cas, humidité) et du niveau de risque ;
  - `epi`    : seuils épidémiques par (district, mois) ;
  - `alerte` : seuils d'alerte par (district, mois).

Le résultat est mis en cache pour éviter de recalculer les prévisions à
chaque interaction.
"""

import numpy as np
import pandas as pd
import streamlit as st

from src import config
from src.data_loader import charger_modeles, charger_panel
from src.features import features_cas, features_hum
from src.forecast_2026 import prevoir_2026
from src.thresholds import calcul_seuils, niveau_risque


@st.cache_data(show_spinner="Calcul des prévisions…")
def preparer():
    """Charge tout, calcule les prévisions et classe le niveau de risque."""
    panel = charger_panel()
    m_cas, m_hum = charger_modeles()
    epi, alerte = calcul_seuils(panel)

    # --- Prévision des cas (cible log-transformée -> expm1, bornée à 0) ---
    fc = features_cas(panel).dropna().reset_index(drop=True)
    fc["pred_cas"] = np.clip(
        np.expm1(m_cas["modele"].predict(fc[m_cas["features"]].values)), 0, None
    ).round()

    # --- Prévision de l'humidité ---
    fh = features_hum(panel).dropna().reset_index(drop=True)
    fh["pred_hum"] = m_hum["modele"].predict(fh[m_hum["features"]].values).round(1)

    # --- Fusion des prévisions dans le panel ---
    P = panel.merge(fc[["district", "date", "pred_cas"]], on=["district", "date"], how="left")
    P = P.merge(fh[["district", "date", "pred_hum"]], on=["district", "date"], how="left")
    P["mois"] = P["date"].dt.month

    # --- Classification du niveau de risque ---
    niveaux = P.apply(
        lambda r: niveau_risque(r["pred_cas"], r["district"], r["mois"], epi, alerte)
        if pd.notna(r["pred_cas"])
        else ("—", config.COULEUR_INCONNU),
        axis=1,
    )
    P[["niveau", "couleur"]] = pd.DataFrame(niveaux.tolist(), index=P.index)

    # --- Projection 2026 (prévision récursive, climat = normales mensuelles) ---
    # Calculée ici car preparer() est mis en cache : la récursion mois par mois
    # n'est donc exécutée qu'une seule fois.
    prev26 = prevoir_2026(panel, m_cas, annee=config.ANNEE_PROJECTION)
    prev26 = prev26.rename(
        columns={"cas_prevu": "pred_cas", "humidite_prevue": "pred_hum"}
    )
    prev26["mois"] = prev26["date"].dt.month
    prev26[["niveau", "couleur"]] = prev26.apply(
        lambda r: pd.Series(
            niveau_risque(r["pred_cas"], r["district"], r["mois"], epi, alerte)
        ),
        axis=1,
    )
    P = pd.concat([P, prev26], ignore_index=True)

    return panel, P, epi, alerte
