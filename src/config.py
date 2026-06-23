"""
Configuration centrale de l'application.

Regroupe les chemins de fichiers, les constantes métier et les métadonnées
affichées dans l'interface. Modifier ce fichier suffit pour adapter
l'application à un nouveau jeu de données ou à de nouveaux modèles.
"""

from pathlib import Path

# ------------------------------------------------------------------ #
#  Chemins
# ------------------------------------------------------------------ #
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

PANEL_PATH = DATA_DIR / "panel_consolide_2017_2025.csv"
MODEL_CAS_PATH = MODELS_DIR / "modele_final_random_forest.pkl"
MODEL_HUM_PATH = MODELS_DIR / "modele_climat_humidite.pkl"

# GeoJSON des limites de district (facultatif : active la carte choroplèthe)
GEOJSON_PATH = DATA_DIR / "districts_extreme_nord.geojson"

# Centre approximatif de la région de l'Extrême-Nord (carte)
CARTE_CENTRE = {"lat": 10.6, "lon": 14.3}
CARTE_ZOOM = 6
CARTE_STYLE = "carto-positron"  # fond de carte sans jeton requis

# Districts de santé sans polygone d'arrondissement, affichés en marqueur
# ponctuel à leurs coordonnées (lat, lon).
DISTRICTS_POINTS = {
    "Mada": {"lat": 11.55, "lon": 14.73},  # localité de l'arrondissement de Makary
}

# ------------------------------------------------------------------ #
#  Variables climatiques utilisées comme prédicteurs
# ------------------------------------------------------------------ #
CLIM = ["temp_moy", "temp_max", "humidite", "precip_mensuel"]

# Date de coupure : les seuils épidémiques sont calculés sur l'historique
# antérieur à cette date (période de référence).
DATE_REFERENCE = "2024-01-01"

# Année projetée au-delà des données observées (prévision récursive).
ANNEE_PROJECTION = 2026

# ------------------------------------------------------------------ #
#  Niveaux de risque (libellé -> couleur)
# ------------------------------------------------------------------ #
COULEUR_EPIDEMIE = "#d62728"
COULEUR_ALERTE = "#ff7f0e"
COULEUR_NORMAL = "#2ca02c"
COULEUR_INCONNU = "#cccccc"

# ------------------------------------------------------------------ #
#  Métadonnées affichées (page Accueil)
# ------------------------------------------------------------------ #
PERIODE = "2017 – 2025"
R2_CAS = "0,872"
R2_HUMIDITE = "0,951"
HORIZON_ALERTE = "2 – 3 mois"
NB_DISTRICTS_THEORIQUE = 33

# Variables proposées dans la page d'exploration
VARIABLES_EXPLORABLES = ["cas", "humidite", "precip_mensuel", "temp_moy", "temp_max"]
