"""
Seuils épidémiques et classification du niveau de risque.

Pour chaque couple (district, mois), deux statistiques sont estimées sur la
période de référence (antérieure à `DATE_REFERENCE`) :
  - le 3e quartile (Q3) des cas historiques ;
  - la moyenne + écart-type des cas historiques.

Convention (canal épidémique à trois niveaux) :
  - seuil d'alerte   = Q3 (dépassement du niveau habituel) ;
  - seuil épidémique = moyenne + écart-type, **borné au minimum par Q3**.

Le bornage garantit `seuil_epidemique >= seuil_alerte` pour tout couple
(district, mois) : sans lui, sur des données de comptage asymétriques où
`moyenne + écart-type > Q3`, le niveau « Alerte » serait inatteignable (toute
valeur dépassant le seuil d'alerte dépasserait aussi le seuil épidémique).

La fonction `niveau_risque` compare une prévision à ces seuils et renvoie
un libellé et une couleur.
"""

import numpy as np

from src import config


def calcul_seuils(df):
    """Retourne (seuil_epidemique, seuil_alerte) indexés par (district, mois)."""
    ref = df[df["date"] < config.DATE_REFERENCE].copy()
    ref["mois"] = ref["date"].dt.month
    g = ref.groupby(["district", "mois"])["cas"]

    q3 = g.quantile(0.75)
    moy_ecart = g.mean() + g.std()

    seuil_alerte = q3
    # seuil épidémique = max(moyenne + écart-type, Q3) — robuste aux NaN d'écart-type
    seuil_epi = moy_ecart.where(moy_ecart >= q3, q3)
    return seuil_epi, seuil_alerte


def niveau_risque(pred, district, mois, epi, alerte):
    """Classe une prévision en Épidémie / Alerte / Normal avec sa couleur."""
    e = epi.get((district, mois), np.inf)
    a = alerte.get((district, mois), np.inf)
    if pred >= e:
        return "Épidémie", config.COULEUR_EPIDEMIE
    if pred >= a:
        return "Alerte", config.COULEUR_ALERTE
    return "Normal", config.COULEUR_NORMAL
