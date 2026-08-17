# Livrables du projet

Le [README](README.md) est la documentation principale. Cette page sert uniquement d'inventaire court des sorties reproductibles.

## Code

- `main_analysis.py` : exécution complète.
- `src/` : chargement, sélection, clustering, scoring, visualisations et rapport.
- `tests/test_analysis.py` : cinq tests unitaires ciblés.
- `requirements.txt` : dépendances réellement utilisées.

## Résultats tabulaires

- `resultats/metriques_modele.json` et `.csv` : métriques du test et de la cross-validation.
- `resultats/selection_variables.csv` : V de Cramer calculés sur le train final.
- `resultats/coefficients_modele.csv` : coefficients log-odds et odds ratios.
- `resultats/evaluation_clustering.csv` : inertie, silhouette et Davies-Bouldin pour `k=2...8`.
- `resultats/profils_clusters.csv` : moyennes et effectifs des trois groupes.
- `resultats/resultats_complets.csv` : scores, prédictions, appartenance train/test et clusters.
- `resultats/analyse_complete.xlsx` : regroupement des tableaux précédents.

## Figures

Le dossier `resultats/figures/` contient dix graphiques générés par le script : distribution de la cible, V de Cramer, association entre variables, diagnostic de `k`, tailles et profils des clusters, matrice de confusion, ROC, coefficients et distribution des scores.

## Rapport

- `RAPPORT_COMPLET.pdf` : rapport universitaire synthétique de sept pages, régénéré à partir des sorties du pipeline.
- `SYNTHESE_RESULTATS.md` : résumé court des résultats reproduits.

Les anciens documents de mise en ligne et guide rapide, redondants avec le README, ne sont pas conservés. Le résumé `statsmodels` a été retiré car il n'utilisait pas le même encodage ni le même périmètre d'entraînement que le pipeline évalué.
