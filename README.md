# 🦟 Surveillance Palustre — Région de l'Extrême-Nord (Cameroun)

Application **Streamlit** d'alerte précoce du paludisme pour la région de
l'Extrême-Nord. Elle s'appuie sur deux modèles **Random Forest** (prévision
des **cas** et de l'**humidité**), au niveau **district** et au pas **mensuel**,
et classe chaque district en *Normal*, *Alerte* ou *Épidémie* selon des seuils
calculés sur l'historique.

> Prototype — mémoire ENSPM Maroua. Reprend la logique de l'application de
> référence (Kenmegne Tertullien), adaptée au présent travail.

---

## ✨ Fonctionnalités

- **Accueil** — vue d'ensemble et indicateurs clés.
- **Charger un fichier** — modèle de saisie téléchargeable (Excel/CSV, 33 districts
  pré-remplis), import **validé** (colonnes, districts, dates, bornes, doublons) et
  mise à jour du panel, + diagnostic des données.
- **Exploration des données** — tableau pivot (date × districts) et séries temporelles.
- **Carte des risques** — choroplèthe des 33 districts (légende, synthèse, source),
  variable au choix, **export PNG**.
- **Prévisions** — prévision des cas et de l'humidité par district.
- **Rapport épidémique** — courbe des seuils (alerte / épidémique) vs prédictions,
  **export PNG** du graphique et **export PDF** du rapport complet.

---

## 📁 Structure du projet

```
PaluAlert/
├── app.py                  # Point d'entrée + navigation
├── requirements.txt
├── README.md
├── data/                   # panel CSV + districts_extreme_nord.geojson
├── models/                 # *.pkl                            (à fournir)
├── scripts/
│   └── preparer_geojson.py # Génère/adapte le GeoJSON des districts
└── src/
    ├── config.py           # Chemins, constantes, métadonnées
    ├── data_loader.py      # Chargement panel + modèles + GeoJSON (caché, robuste)
    ├── features.py         # Ingénierie des variables
    ├── thresholds.py       # Seuils épidémiques + niveau de risque
    ├── pipeline.py         # Orchestration (preparer)
    ├── data_validation.py  # Modèle de saisie + validation des imports
    ├── forecast_2026.py    # Projection récursive au-delà des données
    ├── export_utils.py     # Export PNG des figures (kaleido)
    ├── report_pdf.py       # Génération du rapport PDF (fpdf2)
    └── pages/              # Une page = une fonction render()
        ├── accueil.py
        ├── upload.py
        ├── exploration.py
        ├── carte.py
        ├── previsions.py
        └── rapport.py
```

---

## 🚀 Installation et lancement

```bash
# 1. (recommandé) environnement virtuel
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # macOS / Linux

# 2. dépendances
pip install -r requirements.txt

# 3. déposer les fichiers requis
#    data/panel_consolide_2017_2025.csv
#    models/modele_final_random_forest.pkl
#    models/modele_climat_humidite.pkl

# 4. lancer
streamlit run app.py
```

L'application s'ouvre sur http://localhost:8501.
Si `streamlit` n'est pas dans le PATH : `python -m streamlit run app.py`.

---

## ☁️ Déploiement (Streamlit Community Cloud)

> ⚠️ **Vercel / Netlify ne conviennent pas** : ce sont des plateformes
> *serverless* (fonctions sans état), alors que Streamlit est un **serveur
> persistant** (WebSocket). Utilisez une plateforme qui héberge un serveur.

Déploiement gratuit en quelques clics :

1. Aller sur [share.streamlit.io](https://share.streamlit.io) et se connecter
   avec GitHub.
2. **New app** → dépôt `DAJYO/Palualert`, branche `main`, fichier principal
   `app.py`.
3. **Deploy**. Les dépendances de [`requirements.txt`](requirements.txt) et le
   paquet système de [`packages.txt`](packages.txt) (Chromium, pour les exports
   PNG/PDF) sont installés automatiquement.

Le dépôt contient déjà les données et les modèles : l'application est
fonctionnelle immédiatement après déploiement. Les exports PNG/PDF reposent sur
Chromium installé via `packages.txt` ; en cas d'indisponibilité, l'application
continue de fonctionner et affiche un message clair (dégradation propre).

Autres hébergeurs adaptés (serveur persistant) : Hugging Face Spaces, Render,
Railway.

---

## 📦 Fichiers requis

Voir les README dédiés : [`data/README.md`](data/README.md) et
[`models/README.md`](models/README.md) pour les colonnes et le format des
modèles attendus.

---

## 🧠 Logique de prévision (résumé)

1. Nettoyage du panel (tri, interpolation des cas manquants).
2. Ingénierie des variables : retards climatiques, retards des cas,
   moyenne glissante des précipitations, saisonnalité (sin/cos), id district.
3. Prévision des cas (cible log → `expm1`, bornée à 0) et de l'humidité.
4. Calcul des seuils par (district, mois) sur la période de référence
   (avant `2024-01-01`) : **alerte** = Q3 (3e quartile), **épidémique** =
   moyenne + écart-type (borné au minimum par Q3 pour garantir
   `épidémique ≥ alerte`). Voir [`src/thresholds.py`](src/thresholds.py).
5. Classification du niveau de risque par comparaison aux seuils
   (Normal < Alerte < Épidémie).
6. **Projection 2026** ([`src/forecast_2026.py`](src/forecast_2026.py)) :
   prévision **récursive** mois par mois au-delà des données, le modèle
   existant étant réutilisé (aucun réentraînement). Le climat 2026, non
   observé, est estimé par les **normales mensuelles** par district
   (hypothèse d'« année climatique moyenne »).

> ⚠️ **Limites honnêtes.** (a) La projection 2026 est *conditionnelle* aux
> normales climatiques : une année anormalement humide serait sous-estimée
> (on pourrait brancher un vrai scénario saisonnier à la place). (b) Une
> prévision ne se *valide* qu'a posteriori : la confiance accordée à 2026
> repose sur la performance mesurée en test (2024-2025), années dont la
> vérité est connue.

---

## ⚙️ Configuration

Tous les paramètres modifiables (chemins, variables climatiques, date de
référence, couleurs, métadonnées affichées) sont centralisés dans
[`src/config.py`](src/config.py).
