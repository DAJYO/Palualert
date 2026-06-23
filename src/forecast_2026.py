"""
Projection des cas de paludisme au-delà des données (ex. 2026), par district.

⚠️ Ce module N'ENTRAÎNE AUCUN modèle. Il réutilise le modèle final déjà
entraîné (sur 2017-2023, testé sur 2024-2025) pour PROJETER sur une année
future. La phase de test reste donc intacte.

Principe (prévision récursive — Hyndman, Box-Jenkins) :
  1. Le climat de l'année cible n'est pas observé → on l'estime par les
     normales mensuelles de chaque district (moyenne de chaque mois sur
     l'historique). C'est l'hypothèse d'une « année climatique moyenne » :
     la prévision est conditionnelle à cette hypothèse.
  2. On déroule le modèle mois après mois : chaque cas prédit devient
     l'historique (le retard) du mois suivant.

La projection ne peut être *validée* que lorsque les vrais chiffres de
l'année cible seront disponibles ; la confiance repose sur la performance
mesurée en test (2024-2025).
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

from src.config import CLIM


def prevoir_2026(panel, modele, annee=2026):
    """Projette les 12 mois de `annee` par district (prévision récursive).

    `modele` : dict {"modele": estimateur, "features": [...]} (modèle des cas).
    Retourne un DataFrame : district, date, cas_prevu, humidite_prevue.
    """
    districts = sorted(panel["district"].unique())
    le = LabelEncoder().fit(districts)
    feats = modele["features"]

    # 1) Climat de l'année cible = normales mensuelles par district
    panel = panel.copy()
    panel["mois"] = panel["date"].dt.month
    normales = panel.groupby(["district", "mois"])[CLIM].mean()

    dates = pd.date_range(f"{annee}-01-01", f"{annee}-12-01", freq="MS")
    futur = [
        {"district": d, "date": dt, **normales.loc[(d, dt.month)].to_dict(), "cas": np.nan}
        for d in districts
        for dt in dates
    ]
    full = pd.concat(
        [panel[["district", "date"] + CLIM + ["cas"]], pd.DataFrame(futur)],
        ignore_index=True,
    )
    full = (
        full.sort_values(["district", "date"])
        .set_index(["district", "date"])
        .sort_index()
    )

    cas = full["cas"].to_dict()
    clim = full[CLIM]

    def cl(d, dt, v):
        try:
            return clim.loc[(d, dt), v]
        except KeyError:
            return np.nan

    # 2) Prévision récursive, mois après mois
    for dt in dates:
        X, cles = [], []
        for d in districts:
            r = {v: cl(d, dt, v) for v in CLIM}
            for k in [1, 2, 3, 6]:
                dk = dt - pd.DateOffset(months=k)
                for v in CLIM:
                    r[f"{v}_lag{k}"] = cl(d, dk, v)
            for k in [1, 2, 3, 12]:
                r[f"cas_lag{k}"] = cas.get((d, dt - pd.DateOffset(months=k)), np.nan)
            r["precip_roll3"] = np.nanmean(
                [cl(d, dt - pd.DateOffset(months=j), "precip_mensuel") for j in [2, 1, 0]]
            )
            r["month_sin"] = np.sin(2 * np.pi * dt.month / 12)
            r["month_cos"] = np.cos(2 * np.pi * dt.month / 12)
            r["district_id"] = le.transform([d])[0]
            X.append([r[f] for f in feats])
            cles.append((d, dt))
        pred = np.clip(np.expm1(modele["modele"].predict(np.array(X))), 0, None)
        for cle, p in zip(cles, pred):  # réinjection (récursivité)
            cas[cle] = round(float(p))

    # 3) Mise en forme
    res = pd.DataFrame(
        [
            {
                "district": d,
                "date": dt,
                "cas_prevu": int(cas[(d, dt)]),
                "humidite_prevue": round(cl(d, dt, "humidite"), 1),
            }
            for d in districts
            for dt in dates
        ]
    )
    return res


if __name__ == "__main__":
    # Exécution autonome : écrit prevision_<annee>.csv et affiche le total régional
    import joblib

    from src import config

    panel = pd.read_csv(config.PANEL_PATH)
    panel["date"] = pd.to_datetime(panel["date"])
    panel = panel.sort_values(["district", "date"]).reset_index(drop=True)
    panel["cas"] = panel.groupby("district")["cas"].transform(
        lambda s: s.interpolate(limit_direction="both")
    )
    modele = joblib.load(config.MODEL_CAS_PATH)

    annee = 2026
    prev = prevoir_2026(panel, modele, annee=annee)
    sortie = config.DATA_DIR / f"prevision_{annee}.csv"
    prev.to_csv(sortie, index=False)

    total = prev.groupby("date")["cas_prevu"].sum()
    print(f"=== Prevision des cas - {annee} (total regional) ===")
    for dt, v in total.items():
        print(f"  {dt.strftime('%Y-%m')} : {int(v):>7d} cas")
    print(f"\nTotal {annee} : {int(total.sum()):,} cas".replace(",", " "))
    print(f"\nFichier ecrit : {sortie}")
