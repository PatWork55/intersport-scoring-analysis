# 🎯 Prédiction d'Adhésion & Scoring Client (Cas Intersport)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Scikit-Learn](https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-orange)
![Status](https://img.shields.io/badge/Status-Completed-green)

> 📄 **[Consulter le Rapport d'Analyse Complet (PDF)](./RAPPORT.pdf)**

## 📌 Contexte du Projet
Dans le cadre du lancement d'une nouvelle carte de fidélité, ce projet vise à analyser une base de données clients pour rationaliser la stratégie marketing. L'objectif est double : **identifier les profils types** de la clientèle et **développer un algorithme de scoring** capable de prédire la probabilité d'adhésion d'un client.

## 🚀 Résultats Clés
Ce projet a permis de livrer un outil d'aide à la décision performant :

* **Précision du Modèle (Accuracy) :** `85.33 %`
* **Fiabilité (Pseudo R²) :** `0.51` (Excellente explication de la variance comportementale).
* **Insight Stratégique :** Le ciblage doit prioriser les **femmes de <30 ans pratiquant en club**. La fréquence de visite seule n'est pas un facteur déterminant si elle n'est pas corrélée à l'âge.

## ⚙️ Méthodologie Technique

Le projet suit un pipeline de Data Science rigoureux :

### 1. Audit & Nettoyage
* Vérification de la cohérence des données (225 observations).
* Traitement des valeurs manquantes et encodage.

### 2. Sélection de Variables (Feature Selection)
* Utilisation du **V de Cramer** pour mesurer l'intensité des liens entre les variables qualitatives.
* Sélection des **7 meilleurs prédicteurs** (dont Club, Âge, Budget) et élimination des variables redondantes (Multicolinéarité).

### 3. Segmentation (Clustering K-Means)
Identification de 3 personas clients distincts :
* 🟢 **Les Ambassadeurs :** Jeunes, sportifs licenciés, fort budget (Cœur de cible).
* 🔴 **Les Réfractaires :** Clients âgés, fidèles par habitude mais opposés au programme.
* 🟡 **Les Volatils :** Nouveaux clients en phase de découverte.

### 4. Modélisation (Régression Logistique)
* Entraînement d'un modèle supervisé pour calculer la probabilité d'appétence (Score entre 0 et 1).
* Analyse des coefficients pour quantifier l'impact de chaque variable (ex: *Être membre d'un club augmente significativement le score*).

## 🛠 Technologies Utilisées
* **Langage :** Python
* **Manipulation de données :** Pandas, NumPy
* **Visualisation :** Matplotlib, Seaborn
* **Machine Learning :** Scikit-learn (KMeans, Preprocessing)
* **Statistiques avancées :** Statsmodels (Logit), SciPy (Chi-2)

## 📂 Structure du Dépôt

```text
├── 📓 analysis_notebook.ipynb    # Le code complet (Audit, Vizu, Clustering, Scoring)
├── 📄 Rapport.pdf        # Le rapport managérial détaillé
├── 🗑 .gitignore                 # Exclusion des données brutes
└── 📜 README.md                  # Ce fichier