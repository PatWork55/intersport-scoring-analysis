# Synthèse des résultats

Dernière exécution : **17 août 2026** — `random_state=42`.

Cette synthèse reprend uniquement les sorties générées par `python main_analysis.py`. Le contexte, les choix et les limites sont détaillés dans le [README](README.md), document principal du projet.

## Scoring supervisé

Le split stratifié est effectué avant la sélection. Le V de Cramer, le `OneHotEncoder` et la régression logistique sont ajustés sur le train uniquement. La cross-validation réajuste le pipeline complet dans chaque fold du train.

| Métrique sur le test (n=68) | Valeur |
|---|---:|
| Accuracy | 0,765 |
| ROC-AUC | 0,866 |
| Precision — intéressé | 0,750 |
| Recall — intéressé | 0,794 |
| F1-score — intéressé | 0,771 |

Matrice de confusion : `[[25, 9], [7, 27]]` dans l'ordre `[[TN, FP], [FN, TP]]`.

Cross-validation 5-fold sur le train : ROC-AUC **0,813 ± 0,073**. Les résultats complets figurent dans [`resultats/metriques_modele.csv`](resultats/metriques_modele.csv).

Variables sélectionnées sur le train : `Q7`, `Q23`, `Q5`, `Q6`, `Q3`, `Q4`, `Q18`.

Les coefficients sont exprimés en log-odds. Les odds ratios de [`resultats/coefficients_modele.csv`](resultats/coefficients_modele.csv) comparent chaque modalité à sa référence, toutes choses égales par ailleurs. Ils décrivent des associations, pas des effets causaux.

## Segmentation non supervisée

K-Means utilise uniquement `Q4`, `Q18`, `Q21` et `Q23`, après standardisation. `Q10` n'intervient pas dans la formation des groupes.

| Segment | n | Part | Intérêt Q10 observé après clustering |
|---|---:|---:|---:|
| 0 — visiteurs fréquents plutôt jeunes | 94 | 41,8 % | 67,0 % |
| 1 — sportifs à budget plus élevé | 49 | 21,8 % | 81,6 % |
| 2 — visiteurs plus occasionnels | 82 | 36,4 % | 9,8 % |

Pour `k=3` : inertie `539,29`, silhouette `0,256`, Davies-Bouldin `1,360`. La séparation est modérée ; trois groupes constituent un compromis d'interprétation, pas une vérité définitive.

## Lecture raisonnable

Le score peut servir à prioriser des hypothèses de ciblage et les clusters à adapter les messages. Le dataset ne contient ni coûts de campagne ni conversions observées : aucun ROI, taux de conversion futur ou gain budgétaire ne peut être conclu.
