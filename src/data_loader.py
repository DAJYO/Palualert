"""
Chargement des données et des modèles.

Toutes les fonctions sont mises en cache par Streamlit :
  - `@st.cache_data`     pour le panel (données sérialisables) ;
  - `@st.cache_resource` pour les modèles (objets lourds, non sérialisés).

En cas de fichier manquant, un message clair est affiché à l'utilisateur
et l'exécution est interrompue proprement.
"""

import json
import unicodedata

import joblib
import pandas as pd
import streamlit as st

from src import config


def _verifier_fichier(chemin, description):
    """Interrompt l'application avec un message lisible si le fichier manque."""
    if not chemin.exists():
        st.error(
            f"❌ Fichier introuvable : **{description}**\n\n"
            f"Chemin attendu : `{chemin}`\n\n"
            "Vérifiez que le fichier a bien été déposé dans le dossier prévu "
            "(voir le README)."
        )
        st.stop()


@st.cache_data(show_spinner="Chargement du panel consolidé…")
def charger_panel():
    """Charge le panel, trie par district/date et interpole les cas manquants."""
    _verifier_fichier(config.PANEL_PATH, "panel consolidé (CSV)")

    df = pd.read_csv(config.PANEL_PATH)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["district", "date"]).reset_index(drop=True)
    df["cas"] = df.groupby("district")["cas"].transform(
        lambda s: s.interpolate(limit_direction="both")
    )
    return df


@st.cache_resource(show_spinner="Chargement des modèles…")
def charger_modeles():
    """Charge les deux modèles Random Forest (cas et humidité)."""
    _verifier_fichier(config.MODEL_CAS_PATH, "modèle des cas (.pkl)")
    _verifier_fichier(config.MODEL_HUM_PATH, "modèle d'humidité (.pkl)")

    modele_cas = joblib.load(config.MODEL_CAS_PATH)
    modele_hum = joblib.load(config.MODEL_HUM_PATH)
    return modele_cas, modele_hum


# ------------------------------------------------------------------ #
#  GeoJSON (carte choroplèthe — facultatif)
# ------------------------------------------------------------------ #
@st.cache_data(show_spinner="Chargement du fond de carte…")
def charger_geojson():
    """Charge le GeoJSON des districts, ou None s'il est absent."""
    if not config.GEOJSON_PATH.exists():
        return None
    with open(config.GEOJSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def normaliser(nom):
    """Normalise un nom de district : minuscules, sans accents ni espaces parasites."""
    if nom is None:
        return ""
    s = unicodedata.normalize("NFKD", str(nom))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def apparier_districts(geojson, districts):
    """Détecte la propriété portant le nom du district et apparie les noms.

    Retourne (cle, correspondance) où :
      - `cle`           : nom de la propriété du GeoJSON la mieux appariée ;
      - `correspondance`: dict {nom_district_panel -> identifiant brut du GeoJSON}.
    Si aucune propriété ne correspond, retourne (None, {}).
    """
    if not geojson or not geojson.get("features"):
        return None, {}

    cibles = {normaliser(d): d for d in districts}
    meilleure_cle, meilleur_score, meilleure_map = None, -1, {}

    cles_candidates = geojson["features"][0].get("properties", {}).keys()
    for cle in cles_candidates:
        mapping, score = {}, 0
        for feat in geojson["features"]:
            brut = feat.get("properties", {}).get(cle)
            norm = normaliser(brut)
            if norm in cibles:
                mapping[cibles[norm]] = brut
                score += 1
        if score > meilleur_score:
            meilleure_cle, meilleur_score, meilleure_map = cle, score, mapping

    return (meilleure_cle, meilleure_map) if meilleur_score > 0 else (None, {})
