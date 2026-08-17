"""Exécute l'étude de cas de segmentation et de scoring client."""

import json
import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/intersport-matplotlib")

import matplotlib

matplotlib.use("Agg")

import pandas as pd

from src.clustering import CustomerSegmentation
from src.config import (
    CLUSTER_FEATURES,
    CRAMER_V_THRESHOLD,
    CV_FOLDS,
    DATA_FILE,
    DATA_SHEET,
    FIGURES_DIR,
    MAX_CLUSTERS,
    MODEL_MAX_ITER,
    N_CLUSTERS,
    OUTPUT_DIR,
    RANDOM_STATE,
    REPORT_FILE,
    SCORING_EXCLUDED_VARIABLES,
    TARGET_POSITIVE_CODE,
    TARGET_VARIABLE,
    TEST_SIZE,
    TOP_N_FEATURES,
)
from src.data_loader import DataLoader
from src.feature_selection import FeatureSelector
from src.reporting import generate_pdf_report
from src.scoring_model import ScoringModel
from src.visualization import DataVisualizer


def _header(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def _metrics_table(metrics: dict) -> pd.DataFrame:
    rows = []
    for name in ("accuracy", "roc_auc", "precision", "recall", "f1"):
        test_key = "f1_score" if name == "f1" else name
        rows.append(
            {
                "Methode": "Test indépendant",
                "Metrique": name,
                "Moyenne": metrics[test_key],
                "Ecart_type": None,
            }
        )
        rows.append(
            {
                "Methode": f"Cross-validation {CV_FOLDS}-fold sur le train",
                "Metrique": name,
                "Moyenne": metrics[f"cv_{name}_mean"],
                "Ecart_type": metrics[f"cv_{name}_std"],
            }
        )
    return pd.DataFrame(rows)


def main() -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Lance l'analyse complète et régénère tous les livrables calculés."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    visualizer = DataVisualizer(FIGURES_DIR)

    _header("1. Chargement et contrôle des données")
    loader = DataLoader(DATA_FILE, DATA_SHEET)
    loader.load_data()
    audit = loader.audit_data()
    df = loader.clean_data()
    print(
        f"Données : {audit['shape'][0]} lignes, {audit['shape'][1]} colonnes, "
        f"{audit['duplicates']} doublon(s), {audit['missing_values']} valeur(s) manquante(s)."
    )
    print(f"Distribution Q10 : {audit['target_distribution']}")
    visualizer.plot_target_distribution(df, TARGET_VARIABLE)

    _header("2. Segmentation non supervisée")
    segmentation = CustomerSegmentation(df, CLUSTER_FEATURES, RANDOM_STATE)
    cluster_evaluation = segmentation.evaluate_k(MAX_CLUSTERS)
    segmentation.fit(N_CLUSTERS)
    cluster_profiles = segmentation.describe_clusters(
        TARGET_VARIABLE, TARGET_POSITIVE_CODE
    )
    print(cluster_evaluation.round(3).to_string(index=False))
    print("\nProfils des segments :")
    print(cluster_profiles.round(2).to_string())
    visualizer.plot_cluster_evaluation(cluster_evaluation)
    visualizer.plot_cluster_sizes(segmentation.df)
    visualizer.plot_cluster_profiles(segmentation.standardized_profiles)

    _header("3. Scoring supervisé")
    candidate_features = loader.get_feature_variables(SCORING_EXCLUDED_VARIABLES)
    scoring = ScoringModel(
        df,
        candidate_features,
        target=TARGET_VARIABLE,
        positive_code=TARGET_POSITIVE_CODE,
        random_state=RANDOM_STATE,
    )
    scoring.prepare_data(TEST_SIZE)
    scoring.fit(TOP_N_FEATURES, CRAMER_V_THRESHOLD, MODEL_MAX_ITER)
    metrics = scoring.evaluate(CV_FOLDS)
    selection_results = scoring.get_selection_results()
    selection_results["Selectionnee"] = selection_results["Variable"].isin(
        scoring.selected_features
    )
    importance = scoring.get_feature_importance()

    print(f"Train : {len(scoring.X_train)} observations ; test : {len(scoring.X_test)}.")
    print(f"Variables sélectionnées sur le train : {scoring.selected_features}")
    print(
        "Test — "
        f"accuracy={metrics['accuracy']:.3f}, ROC-AUC={metrics['roc_auc']:.3f}, "
        f"precision={metrics['precision']:.3f}, recall={metrics['recall']:.3f}, "
        f"F1={metrics['f1_score']:.3f}"
    )
    print(
        f"Cross-validation sur le train — ROC-AUC="
        f"{metrics['cv_roc_auc_mean']:.3f} ± {metrics['cv_roc_auc_std']:.3f}"
    )
    print(f"Matrice de confusion :\n{metrics['confusion_matrix']}")

    selector = FeatureSelector(
        scoring.X_train.assign(__target__=scoring.y_train), "__target__"
    )
    selector.compute_associations(scoring.selected_features)
    association_matrix = selector.check_multicollinearity(scoring.selected_features)

    visualizer.plot_cramers_v(selection_results)
    visualizer.plot_correlation_matrix(association_matrix)
    visualizer.plot_confusion_matrix(metrics["confusion_matrix"])
    visualizer.plot_roc_curve(scoring.y_test, metrics["test_probabilities"])
    visualizer.plot_feature_importance(importance)

    _header("4. Scores et exports")
    scores = scoring.predict_score()
    predictions = scoring.predict()
    visualizer.plot_score_distribution(scores)

    results = df[["obs", TARGET_VARIABLE] + scoring.selected_features].copy()
    results["Jeu"] = "train"
    results.loc[scoring.X_test.index, "Jeu"] = "test"
    results["Cluster"] = segmentation.labels_
    results["Score_Propension"] = scores
    results["Prediction"] = predictions
    results["Interet_Carte"] = df[TARGET_VARIABLE].map({1: "Oui", 2: "Non"})
    results["Prediction_Interet"] = predictions.map({1: "Oui", 0: "Non"})

    metrics_table = _metrics_table(metrics)
    confusion_table = pd.DataFrame(
        metrics["confusion_matrix"],
        index=["Reel_Non", "Reel_Oui"],
        columns=["Predit_Non", "Predit_Oui"],
    )

    results.to_csv(OUTPUT_DIR / "resultats_complets.csv", index=False)
    selection_results.to_csv(OUTPUT_DIR / "selection_variables.csv", index=False)
    importance.to_csv(OUTPUT_DIR / "coefficients_modele.csv", index=False)
    cluster_evaluation.to_csv(OUTPUT_DIR / "evaluation_clustering.csv", index=False)
    cluster_profiles.to_csv(OUTPUT_DIR / "profils_clusters.csv")
    metrics_table.to_csv(OUTPUT_DIR / "metriques_modele.csv", index=False)

    json_metrics = {
        key: value
        for key, value in metrics.items()
        if key not in {"confusion_matrix", "test_predictions", "test_probabilities"}
    }
    json_metrics["confusion_matrix"] = metrics["confusion_matrix"].tolist()
    json_metrics["selected_features"] = scoring.selected_features
    with (OUTPUT_DIR / "metriques_modele.json").open("w", encoding="utf-8") as file:
        json.dump(json_metrics, file, ensure_ascii=False, indent=2)

    with pd.ExcelWriter(OUTPUT_DIR / "analyse_complete.xlsx", engine="openpyxl") as writer:
        results.to_excel(writer, sheet_name="Scores et segments", index=False)
        metrics_table.to_excel(writer, sheet_name="Métriques", index=False)
        confusion_table.to_excel(writer, sheet_name="Matrice confusion")
        selection_results.to_excel(writer, sheet_name="Sélection train", index=False)
        importance.to_excel(writer, sheet_name="Coefficients", index=False)
        cluster_evaluation.to_excel(writer, sheet_name="Choix k", index=False)
        cluster_profiles.to_excel(writer, sheet_name="Profils segments")

    generate_pdf_report(
        REPORT_FILE,
        metrics,
        selection_results,
        importance,
        cluster_evaluation,
        cluster_profiles,
        FIGURES_DIR,
    )
    print(f"Résultats écrits dans : {OUTPUT_DIR}")
    print(f"Rapport régénéré : {REPORT_FILE}")
    return results, metrics, cluster_profiles


if __name__ == "__main__":
    main()
