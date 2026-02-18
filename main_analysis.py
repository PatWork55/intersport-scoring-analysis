"""
Script principal d'analyse complète - Projet Intersport
Scoring et Segmentation Client

Ce script orchestre toute l'analyse:
1. Chargement et audit des données
2. Sélection de variables (V de Cramer)
3. Segmentation client (K-Means)
4. Modèle de scoring (Régression Logistique)
5. Visualisations et exports
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

# Import des modules du projet
from src.data_loader import DataLoader
from src.feature_selection import FeatureSelector
from src.clustering import CustomerSegmentation
from src.scoring_model import ScoringModel
from src.visualization import DataVisualizer
from src.config import *

import pandas as pd
import numpy as np


def print_header(title: str):
    """Affiche un en-tête formaté"""
    print("\n" + "="*90)
    print(f"  {title}")
    print("="*90 + "\n")


def main():
    """Fonction principale orchestrant toute l'analyse"""

    print("\n" + "█"*90)
    print("█" + " "*88 + "█")
    print("█" + " "*20 + "ANALYSE INTERSPORT - SCORING CLIENT" + " "*35 + "█")
    print("█" + " "*88 + "█")
    print("█"*90 + "\n")

    # Créer les répertoires de sortie
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    # ========================================================================
    # ÉTAPE 1: CHARGEMENT ET AUDIT DES DONNÉES
    # ========================================================================
    print_header("ÉTAPE 1: CHARGEMENT ET AUDIT DES DONNÉES")

    loader = DataLoader(DATA_FILE)
    df = loader.load_data()

    # Audit complet
    audit_results = loader.audit_data()
    loader.print_audit_report(audit_results)

    # Nettoyage
    df_clean = loader.clean_data(remove_duplicates=True)

    # Visualisation de la cible
    viz = DataVisualizer(FIGURES_DIR)
    viz.plot_target_distribution(df_clean, TARGET_VARIABLE)

    # ========================================================================
    # ÉTAPE 2: SÉLECTION DE VARIABLES (V de Cramer)
    # ========================================================================
    print_header("ÉTAPE 2: SÉLECTION DE VARIABLES (V de Cramer)")

    # Liste des features (excluant ID, cible, et variables de leakage)
    all_features = loader.get_feature_variables(exclude=LEAK_VARIABLES)

    # Calcul des associations
    selector = FeatureSelector(df_clean, TARGET_VARIABLE)
    results_df = selector.compute_associations(all_features)

    # Affichage des résultats
    selector.print_results(n=20)

    # Visualisation
    viz.plot_cramers_v(results_df, top_n=15)

    # Sélection des top variables
    top_features = selector.get_top_features(n=10, threshold=CRAMER_V_THRESHOLD)
    print(f"\n✓ Variables sélectionnées pour la suite: {top_features}\n")

    # Vérification de la multicolinéarité
    print("\n📊 Analyse de multicolinéarité entre les variables sélectionnées...")
    corr_matrix = selector.check_multicollinearity(top_features)
    print(corr_matrix.round(3))
    viz.plot_correlation_matrix(corr_matrix)

    # Export des résultats de sélection
    results_df.to_csv(os.path.join(OUTPUT_DIR, 'selection_variables.csv'), index=False)
    print(f"\n✓ Résultats exportés: {OUTPUT_DIR}selection_variables.csv")

    # ========================================================================
    # ÉTAPE 3: SEGMENTATION CLIENT (K-Means)
    # ========================================================================
    print_header("ÉTAPE 3: SEGMENTATION CLIENT (K-Means)")

    # Initialisation de la segmentation
    segmentation = CustomerSegmentation(df_clean, top_features[:8])

    # Méthode du coude pour choisir k
    print("\n🔍 Recherche du nombre optimal de clusters...")
    elbow_results = segmentation.find_optimal_clusters(max_k=8)
    viz.plot_elbow_method(elbow_results)

    # Clustering avec k=3 (décision basée sur l'analyse)
    print(f"\n✓ Application de K-Means avec {N_CLUSTERS} clusters...")
    segmentation.fit_kmeans(n_clusters=N_CLUSTERS)

    # Profils des clusters
    cluster_profiles = segmentation.describe_clusters()

    # Distribution de la cible par cluster
    target_by_cluster = segmentation.analyze_target_by_cluster(TARGET_VARIABLE)

    # Interprétation des clusters
    interpretations = segmentation.get_cluster_interpretation(TARGET_VARIABLE)
    print("\n📊 INTERPRÉTATION DES CLUSTERS:")
    print("="*80)
    for cluster_id, info in interpretations.items():
        print(f"\nCluster {cluster_id}: {info['Catégorie']}")
        print(f"  • Taux d'intérêt pour la carte: {info['Taux_Interet']}")
        print(f"  • Effectif: {info['Effectif']} clients ({info['Pourcentage']} de la base)")

    # Visualisations
    viz.plot_cluster_sizes(segmentation.df)
    viz.plot_cluster_profiles(cluster_profiles)

    # Export des résultats de clustering
    df_with_clusters = segmentation.df.copy()
    cluster_profiles.to_csv(os.path.join(OUTPUT_DIR, 'profils_clusters.csv'))
    print(f"\n✓ Profils des clusters exportés: {OUTPUT_DIR}profils_clusters.csv")

    # ========================================================================
    # ÉTAPE 4: MODÈLE DE SCORING (Régression Logistique)
    # ========================================================================
    print_header("ÉTAPE 4: MODÈLE DE SCORING (Régression Logistique)")

    # Initialisation du modèle
    scoring = ScoringModel(df_clean, top_features[:7], TARGET_VARIABLE)

    # Préparation des données
    scoring.prepare_data(test_size=TEST_SIZE, encode_dummies=True)

    # Entraînement du modèle scikit-learn
    print("\n🔧 Entraînement du modèle scikit-learn...")
    scoring.fit_sklearn_model(max_iter=MODEL_MAX_ITER)

    # Évaluation
    metrics = scoring.evaluate_model()
    scoring.print_evaluation(metrics)

    # Importance des variables
    scoring.print_feature_importance(top_n=20)

    # Visualisations du modèle
    viz.plot_confusion_matrix(metrics['confusion_matrix'])

    # Courbe ROC
    y_pred_proba = scoring.model.predict_proba(scoring.X_test)[:, 1]
    viz.plot_roc_curve(scoring.y_test, y_pred_proba)

    # Importance des features
    importance_df = scoring.get_feature_importance()
    viz.plot_feature_importance(importance_df, top_n=15)

    # ========================================================================
    # ÉTAPE 5: CALCUL DES SCORES DE PROPENSION
    # ========================================================================
    print_header("ÉTAPE 5: CALCUL DES SCORES DE PROPENSION")

    print("\n🎯 Calcul des scores pour tous les clients...")
    scores = scoring.predict_score()

    # Ajout des scores au DataFrame
    df_final = df_clean.copy()
    df_final['Score_Propension'] = scores
    df_final['Cluster'] = df_with_clusters['Cluster']
    df_final['Prediction'] = (scores > 0.5).astype(int)

    # Statistiques des scores
    print(f"\n📊 Statistiques des scores:")
    print(f"   • Moyenne: {scores.mean():.4f}")
    print(f"   • Médiane: {scores.median():.4f}")
    print(f"   • Écart-type: {scores.std():.4f}")
    print(f"   • Min: {scores.min():.4f}")
    print(f"   • Max: {scores.max():.4f}")

    # Visualisation des scores
    viz.plot_score_distribution(scores)

    # ========================================================================
    # ÉTAPE 6: MODÈLE STATSMODELS (pour rapport détaillé)
    # ========================================================================
    print_header("ÉTAPE 6: STATISTIQUES DÉTAILLÉES (statsmodels)")

    print("\n🔧 Entraînement du modèle statsmodels pour statistiques avancées...")
    statsmodels_result = scoring.fit_statsmodels()

    # Sauvegarde du résumé
    summary_text = scoring.get_statsmodels_summary()
    with open(os.path.join(OUTPUT_DIR, 'modele_statistiques.txt'), 'w') as f:
        f.write(summary_text)

    print(f"\n✓ Statistiques détaillées exportées: {OUTPUT_DIR}modele_statistiques.txt")

    # Affichage d'un extrait
    print("\n" + "-"*80)
    print("EXTRAIT DU RÉSUMÉ STATSMODELS:")
    print("-"*80)
    print(summary_text)

    # ========================================================================
    # ÉTAPE 7: EXPORTS FINAUX
    # ========================================================================
    print_header("ÉTAPE 7: EXPORTS DES RÉSULTATS")

    # Export principal avec tous les résultats
    export_cols = ['obs', TARGET_VARIABLE] + top_features[:7] + ['Cluster', 'Score_Propension', 'Prediction']
    df_export = df_final[export_cols].copy()

    # Ajout d'étiquettes lisibles
    df_export['Interet_Carte'] = df_export[TARGET_VARIABLE].map({1: 'Oui', 2: 'Non'})
    df_export['Prediction_Interet'] = df_export['Prediction'].map({1: 'Oui', 0: 'Non'})

    # Export CSV
    output_file = os.path.join(OUTPUT_DIR, 'resultats_complets.csv')
    df_export.to_csv(output_file, index=False)
    print(f"\n✓ Résultats complets exportés: {output_file}")

    # Export Excel avec plusieurs feuilles
    excel_file = os.path.join(OUTPUT_DIR, 'analyse_complete.xlsx')
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df_export.to_excel(writer, sheet_name='Résultats', index=False)
        results_df.to_excel(writer, sheet_name='Sélection Variables', index=False)
        cluster_profiles.to_excel(writer, sheet_name='Profils Clusters')
        importance_df.to_excel(writer, sheet_name='Importance Variables', index=False)

    print(f"✓ Fichier Excel complet exporté: {excel_file}")

    # Synthèse des exports
    print("\n" + "="*90)
    print("SYNTHÈSE DES FICHIERS GÉNÉRÉS")
    print("="*90)
    print(f"\n📁 Répertoire des résultats: {OUTPUT_DIR}")
    print(f"   • resultats_complets.csv - Données avec scores et clusters")
    print(f"   • analyse_complete.xlsx - Tous les résultats en un fichier Excel")
    print(f"   • selection_variables.csv - Résultats du V de Cramer")
    print(f"   • profils_clusters.csv - Caractéristiques des segments")
    print(f"   • modele_statistiques.txt - Statistiques détaillées du modèle")

    print(f"\n📊 Répertoire des graphiques: {FIGURES_DIR}")
    print(f"   • target_distribution.png - Distribution de la variable cible")
    print(f"   • cramers_v_ranking.png - Classement des variables")
    print(f"   • correlation_matrix.png - Matrice de corrélation")
    print(f"   • elbow_method.png - Choix du nombre de clusters")
    print(f"   • cluster_sizes.png - Taille des clusters")
    print(f"   • cluster_profiles.png - Profils des segments")
    print(f"   • confusion_matrix.png - Performance du modèle")
    print(f"   • roc_curve.png - Courbe ROC")
    print(f"   • feature_importance.png - Importance des variables")
    print(f"   • score_distribution.png - Distribution des scores")

    # ========================================================================
    # CONCLUSION
    # ========================================================================
    print("\n" + "█"*90)
    print("█" + " "*88 + "█")
    print("█" + " "*25 + "ANALYSE TERMINÉE AVEC SUCCÈS" + " "*37 + "█")
    print("█" + " "*88 + "█")
    print("█"*90 + "\n")

    print(f"✓ Tous les résultats et visualisations ont été générés avec succès!")
    print(f"✓ Consultez le rapport détaillé pour l'interprétation complète.")
    print(f"\n📈 Métriques clés:")
    print(f"   • Accuracy du modèle: {metrics['accuracy']:.2%}")
    print(f"   • ROC AUC Score: {metrics['roc_auc']:.4f}")
    print(f"   • Nombre de clusters: {N_CLUSTERS}")
    print(f"   • Variables prédictives: {len(top_features[:7])}")

    return df_final, metrics, cluster_profiles


if __name__ == "__main__":
    try:
        df_final, metrics, clusters = main()
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
