"""
Préparation du GeoJSON des districts de l'Extrême-Nord.

Construit `data/districts_extreme_nord.geojson` à partir des limites
administratives ADM3 (arrondissements) du Cameroun publiées par geoBoundaries.

Étapes :
  1. lecture du GeoJSON source (ADM3 Cameroun) ;
  2. correction du double-encodage UTF-8 (mojibake) des noms ;
  3. sélection + renommage des arrondissements pour coller aux noms de
     district de santé du panel (table `CORRESPONDANCE`) ;
  4. écriture du GeoJSON final avec la propriété `district`.

Source : geoBoundaries gbOpen, Cameroun ADM3 (simplifié).
  https://www.geoboundaries.org/  (licence ouverte, attribution requise)

Limites connues : les districts de santé « Mada » et « Vele » n'ont pas
d'arrondissement correspondant et ne peuvent donc pas être cartographiés à
cette résolution. Ils seront signalés comme « non localisés » par l'app.

Usage :
    python scripts/preparer_geojson.py [chemin_source.geojson]

Si aucun chemin n'est fourni, le script tente d'utiliser
`_geo_tmp/cmr_adm3.geojson` puis, à défaut, télécharge la source.
"""

import json
import sys
import unicodedata
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SORTIE = BASE_DIR / "data" / "districts_extreme_nord.geojson"
SOURCE_LOCALE = BASE_DIR / "_geo_tmp" / "cmr_adm3.geojson"
SOURCE_URL = (
    "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/"
    "releaseData/gbOpen/CMR/ADM3/geoBoundaries-CMR-ADM3_simplified.geojson"
)

# Correspondance : nom de district (panel) -> nom d'arrondissement (source).
# Quand les deux noms sont identiques après normalisation, on répète le nom
# pour garder la table explicite et auditable.
CORRESPONDANCE = {
    "Bogo": "Bogo",
    "Bourha": "Bourha",
    "Fotokol": "Fotokol",
    "Gazawa": "Gazawa",
    "Goulfey": "Goulfey",
    "Guere": "Guéré",
    "Guidiguis": "Guidiguis",
    "Hina": "Hina",
    "Kaele": "Kaélé",
    "Kar Hay": "Kar-Hay",
    "Kolofata": "Kolofata",
    "Kousseri": "Kousséri",
    "Koza": "Koza",
    "Maga": "Maga",
    "Makary": "Makary",
    "Maroua 1": "Maroua I",
    "Maroua 2": "Maroua II",
    "Maroua 3": "Maroua III",
    "Meri": "Meri",
    "Mindif": "Mindif",
    "Mogode": "Mogodé",
    "Mokolo": "Mokolo",
    "Mora": "Mora",
    "Moulvoudaye": "Moulvoudaye",
    "Moutourwa": "Moutourwa",
    "Mozogo": "Mozogo",
    "Pette": "Pétté",
    "Roua": "Soulédé-Roua",
    "Tokombere": "Tokombéré",
    "Vele": "Guémé",  # arrondissement de Vélé, nommé d'après son chef-lieu Guémé
    "Waza": "Waza",
    "Yagoua": "Yagoua",
    # "Mada" : localité de l'arrondissement de Makary, sans polygone propre.
    #          Représenté par un point (voir config.DISTRICTS_POINTS).
}

# Districts de santé sans polygone d'arrondissement (affichés en marqueur)
SANS_POLYGONE = ["Mada"]


def corriger_mojibake(s):
    """Répare un texte UTF-8 lu par erreur en Latin-1 (« é » -> « Ã© »)."""
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def normaliser(nom):
    """minuscules, sans accents, tirets -> espaces, espaces compactés."""
    s = unicodedata.normalize("NFKD", str(nom)).replace("-", " ")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def charger_source(chemin_cli):
    if chemin_cli:
        src = Path(chemin_cli)
    elif SOURCE_LOCALE.exists():
        src = SOURCE_LOCALE
    else:
        SOURCE_LOCALE.parent.mkdir(parents=True, exist_ok=True)
        print(f"Téléchargement de la source…\n  {SOURCE_URL}")
        urllib.request.urlretrieve(SOURCE_URL, SOURCE_LOCALE)
        src = SOURCE_LOCALE
    print(f"Source : {src}")
    with open(src, encoding="utf-8") as f:
        return json.load(f)


def main():
    chemin_cli = sys.argv[1] if len(sys.argv) > 1 else None
    geojson = charger_source(chemin_cli)

    # Index des features source par nom normalisé (après correction mojibake)
    index = {}
    for feat in geojson["features"]:
        nom = corriger_mojibake(feat["properties"].get("shapeName", ""))
        index[normaliser(nom)] = feat

    features, absents = [], []
    for district, arrondissement in CORRESPONDANCE.items():
        feat = index.get(normaliser(arrondissement))
        if feat is None:
            absents.append((district, arrondissement))
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {"district": district, "source": arrondissement},
                "geometry": feat["geometry"],
            }
        )

    sortie = {"type": "FeatureCollection", "features": features}
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    with open(SORTIE, "w", encoding="utf-8") as f:
        json.dump(sortie, f, ensure_ascii=False)

    print(f"\n[OK] Ecrit : {SORTIE}")
    print(f"   Districts polygones : {len(features)}/33")
    print(f"   En marqueur (sans polygone) : {', '.join(SANS_POLYGONE)}")
    if absents:
        print("   [!] Correspondances introuvables dans la source :")
        for d, a in absents:
            print(f"      {d} -> {a}")


if __name__ == "__main__":
    main()
