# Dossier `models/`

Déposez ici les deux modèles entraînés (format `joblib`) :

```
models/modele_final_random_forest.pkl   # prévision des cas
models/modele_climat_humidite.pkl       # prévision de l'humidité
```

## Format attendu

Chaque fichier `.pkl` doit contenir un **dictionnaire** avec au moins :

| Clé        | Contenu                                                        |
|------------|---------------------------------------------------------------|
| `modele`   | L'estimateur scikit-learn entraîné (avec une méthode `.predict`) |
| `features` | La liste ordonnée des noms de colonnes attendues en entrée    |

Exemple de sauvegarde côté entraînement :

```python
import joblib
joblib.dump({"modele": rf, "features": liste_features},
            "models/modele_final_random_forest.pkl")
```

> Le modèle des cas prédit la cible **log-transformée** : l'application
> applique `np.expm1` puis borne le résultat à 0.
