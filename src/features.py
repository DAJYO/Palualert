"""
Ingénierie des variables (feature engineering).

Reproduit fidèlement la logique de l'application de référence :
  - `features_cas`  : retards climatiques (1,2,3,6 mois), retards des cas
                      (1,2,3,12 mois), moyenne glissante des précipitations,
                      saisonnalité (sin/cos) et identifiant de district ;
  - `features_hum`  : retards climatiques (1,2,3,12 mois), saisonnalité et
                      identifiant de district.
"""

import numpy as np
from sklearn.preprocessing import LabelEncoder

from src.config import CLIM


def _ajouter_saisonnalite(df):
    """Ajoute les composantes cycliques du mois (sin/cos)."""
    m = df["date"].dt.month
    df["month_sin"] = np.sin(2 * np.pi * m / 12)
    df["month_cos"] = np.cos(2 * np.pi * m / 12)
    return df


def features_cas(df):
    """Construit les variables d'entrée du modèle de prévision des cas."""
    df = df.copy()
    g = df.groupby("district")

    for k in [1, 2, 3, 6]:
        for v in CLIM:
            df[f"{v}_lag{k}"] = g[v].shift(k)

    for k in [1, 2, 3, 12]:
        df[f"cas_lag{k}"] = g["cas"].shift(k)

    df["precip_roll3"] = g["precip_mensuel"].transform(lambda s: s.rolling(3).mean())

    df = _ajouter_saisonnalite(df)
    df["district_id"] = LabelEncoder().fit_transform(df["district"])
    return df


def features_hum(df):
    """Construit les variables d'entrée du modèle de prévision d'humidité."""
    df = df.copy()
    g = df.groupby("district")

    for k in [1, 2, 3, 12]:
        for v in CLIM:
            df[f"{v}_lag{k}"] = g[v].shift(k)

    df = _ajouter_saisonnalite(df)
    df["district_id"] = LabelEncoder().fit_transform(df["district"])
    return df
