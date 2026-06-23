# Dossier `data/`

Déposez ici le panel consolidé :

```
data/panel_consolide_2017_2025.csv
```

Colonnes attendues (au minimum) :

| Colonne          | Description                                  |
|------------------|----------------------------------------------|
| `district`       | Nom du district sanitaire                    |
| `date`           | Date mensuelle (format reconnu par pandas)   |
| `cas`            | Nombre de cas de paludisme                   |
| `temp_moy`       | Température moyenne                           |
| `temp_max`       | Température maximale                          |
| `humidite`       | Humidité (%)                                 |
| `precip_mensuel` | Précipitations mensuelles                    |

## Carte choroplèthe (facultatif)

Pour activer l'onglet **Carte des risques**, déposez le fichier des limites
de district :

```
data/districts_extreme_nord.geojson
```

- Format : **GeoJSON** (`FeatureCollection`), une *feature* par district.
- Chaque *feature* doit porter, dans ses `properties`, le **nom du district**
  (ex. propriété `district`, `NAME`, `nom`, …). L'application détecte
  automatiquement la bonne propriété et apparie les noms de façon insensible
  à la casse et aux accents.
- Les districts dont le nom ne figure pas dans le GeoJSON sont signalés sous
  la carte.

> Sans ce fichier, l'onglet affiche un repli (classement des districts en
> barres) au lieu de la carte.

### Fichier déjà fourni

`districts_extreme_nord.geojson` est **déjà présent** : il a été généré à
partir des limites administratives **ADM3 (arrondissements)** du Cameroun de
[geoBoundaries](https://www.geoboundaries.org/) (gbOpen, licence ouverte —
attribution requise), puis adapté aux noms du panel.

Pour le régénérer (ou repartir d'une autre source) :

```bash
python scripts/preparer_geojson.py            # télécharge la source si besoin
python scripts/preparer_geojson.py source.geojson   # à partir d'un fichier local
```

Le script corrige le double-encodage des accents, sélectionne les
arrondissements de l'Extrême-Nord et les renomme via la table
`CORRESPONDANCE` (ex. `Maroua 1` → `Maroua I`, `Roua` → `Soulédé-Roua`,
`Vele` → `Guémé` — l'arrondissement de Vélé est nommé d'après son chef-lieu).

**33 / 33 districts** sont représentés :

- **32 en polygone** (arrondissements) ;
- **1 en marqueur** : `Mada`, localité de l'arrondissement de Makary sans
  polygone propre, positionnée à ses coordonnées (voir
  `config.DISTRICTS_POINTS`).

Pour afficher des districts de santé supplémentaires en polygone, fournissez
un GeoJSON de santé plus fin et complétez la table `CORRESPONDANCE`.
