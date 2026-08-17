"""Génération d'un rapport PDF court à partir des résultats reproductibles."""

from datetime import date
from pathlib import Path
from textwrap import fill

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages


PAGE_SIZE = (8.27, 11.69)


def _new_page(title: str, page_number: int):
    fig = plt.figure(figsize=PAGE_SIZE)
    fig.patch.set_facecolor("white")
    fig.text(0.08, 0.94, title, fontsize=18, weight="bold", color="#264653")
    fig.text(0.08, 0.035, "Étude de cas académique — Retail sportif", fontsize=8, color="grey")
    fig.text(0.92, 0.035, str(page_number), fontsize=8, color="grey", ha="right")
    return fig


def _paragraph(fig, text: str, y: float, width: int = 98, size: int = 10, **kwargs):
    fig.text(0.08, y, fill(text, width=width), fontsize=size, va="top", linespacing=1.45, **kwargs)


def _add_image(fig, path: Path, bounds: list[float], title: str | None = None):
    axis = fig.add_axes(bounds)
    axis.imshow(plt.imread(path))
    axis.axis("off")
    if title:
        axis.set_title(title, fontsize=10)


def generate_pdf_report(
    output_file: str | Path,
    metrics: dict,
    selection_results: pd.DataFrame,
    importance: pd.DataFrame,
    cluster_evaluation: pd.DataFrame,
    cluster_profiles: pd.DataFrame,
    figures_dir: str | Path,
) -> None:
    """Produit un PDF universitaire synthétique sans chiffres saisis à la main."""
    output_file = Path(output_file)
    figures_dir = Path(figures_dir)
    cm = metrics["confusion_matrix"]

    with PdfPages(
        output_file,
        metadata={
            "Title": "Scoring et segmentation client — Étude de cas Retail",
            "Author": "AFFOUDJI Akomédi Paterne",
            "Subject": "Projet académique de Data Science",
        },
    ) as pdf:
        fig = plt.figure(figsize=PAGE_SIZE)
        fig.patch.set_facecolor("white")
        fig.text(0.5, 0.76, "SCORING ET SEGMENTATION CLIENT", ha="center", fontsize=23, weight="bold", color="#264653")
        fig.text(0.5, 0.68, "Étude de cas Retail / sport", ha="center", fontsize=18, color="#457b9d")
        fig.text(0.5, 0.57, "Projet académique de Data Science", ha="center", fontsize=13)
        fig.text(0.5, 0.48, "K-Means • Régression logistique • Pipeline scikit-learn", ha="center", fontsize=11)
        fig.text(0.5, 0.31, "AFFOUDJI Akomédi Paterne", ha="center", fontsize=11)
        fig.text(0.5, 0.27, date.today().strftime("%d/%m/%Y"), ha="center", fontsize=10, color="grey")
        _paragraph(
            fig,
            "Projet académique / portfolio basé sur une étude de cas dans le secteur du retail sportif. Ce dépôt n'est pas affilié à Intersport.",
            0.15,
            width=82,
            size=9,
            ha="left",
        )
        pdf.savefig(fig)
        plt.close(fig)

        fig = _new_page("1. Cadre et objectifs", 2)
        _paragraph(
            fig,
            "Le fichier rassemble 225 questionnaires et 57 colonnes. La cible Q10 indique si le répondant se déclare intéressé par une carte de fidélité. L'étude répond à deux questions distinctes : décrire des profils de clients sans utiliser la cible, puis estimer la probabilité d'intérêt avec un modèle supervisé.",
            0.87,
        )
        _paragraph(
            fig,
            "Segmentation (non supervisée). K-Means est appliqué à quatre variables ordinales ou quantitatives : fréquence de visite (Q4), tranche d'âge (Q18), budget sport annuel (Q21) et nombre de sports pratiqués (Q23).",
            0.69,
        )
        _paragraph(
            fig,
            "Scoring (supervisé). Une régression logistique estime l'intérêt déclaré. Le split train/test stratifié précède la sélection de variables. Le V de Cramer, le OneHotEncoder et le modèle sont ajustés uniquement sur le train. La cross-validation est elle aussi limitée au train et réajuste l'ensemble du pipeline dans chaque fold.",
            0.53,
        )
        _paragraph(
            fig,
            "Les questions Q11 et Q13 sont conditionnelles à Q10. Q12a-e et Q14 sont également écartées car elles portent directement sur la carte et seraient des proxys trop proches de la cible. Cette décision privilégie une évaluation crédible à une performance artificiellement élevée.",
            0.34,
        )
        _paragraph(
            fig,
            "Les résultats sont associatifs et exploratoires. Ils ne démontrent aucune causalité et ne constituent ni une validation commerciale ni une estimation de ROI.",
            0.16,
            color="#9b2226",
        )
        pdf.savefig(fig)
        plt.close(fig)

        fig = _new_page("2. Résultats du scoring", 3)
        rows = [
            ["Accuracy", f"{metrics['accuracy']:.3f}"],
            ["ROC-AUC", f"{metrics['roc_auc']:.3f}"],
            ["Precision (classe intéressé)", f"{metrics['precision']:.3f}"],
            ["Recall (classe intéressé)", f"{metrics['recall']:.3f}"],
            ["F1-score (classe intéressé)", f"{metrics['f1_score']:.3f}"],
            ["CV ROC-AUC sur le train", f"{metrics['cv_roc_auc_mean']:.3f} ± {metrics['cv_roc_auc_std']:.3f}"],
        ]
        ax = fig.add_axes([0.08, 0.59, 0.84, 0.28])
        ax.axis("off")
        table = ax.table(cellText=rows, colLabels=["Métrique", "Valeur"], loc="center", cellLoc="left")
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.5)
        _paragraph(
            fig,
            f"Matrice de confusion sur les 68 observations du test : TN={cm[0, 0]}, FP={cm[0, 1]}, FN={cm[1, 0]}, TP={cm[1, 1]}. Le jeu de test n'est utilisé qu'à cette étape d'évaluation finale.",
            0.51,
        )
        _add_image(fig, figures_dir / "roc_curve.png", [0.08, 0.09, 0.39, 0.35])
        _add_image(fig, figures_dir / "confusion_matrix.png", [0.53, 0.09, 0.39, 0.35])
        pdf.savefig(fig)
        plt.close(fig)

        fig = _new_page("3. Sélection et interprétation", 4)
        selected = selection_results.loc[selection_results["Selectionnee"], ["Variable", "Cramer_V", "P_Value"]].copy()
        selected["Cramer_V"] = selected["Cramer_V"].map(lambda value: f"{value:.3f}")
        selected["P_Value"] = selected["P_Value"].map(lambda value: f"{value:.3g}")
        ax = fig.add_axes([0.08, 0.56, 0.84, 0.31])
        ax.axis("off")
        table = ax.table(cellText=selected.values, colLabels=["Variable", "V de Cramer", "p-value"], loc="center", cellLoc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(8.5)
        table.scale(1, 1.35)
        _paragraph(
            fig,
            "Le V de Cramer repose sur le test du Chi² et mesure l'association entre deux variables catégorielles. Le seuil de 0,15 est un choix pragmatique pour cette étude. Les p-values sont descriptives : aucune correction pour tests multiples n'est appliquée, et la sélection peut varier sur un autre échantillon.",
            0.50,
        )
        top = importance.head(5)[["Modalite", "Coefficient_log_odds", "Odds_ratio"]].copy()
        top["Coefficient_log_odds"] = top["Coefficient_log_odds"].map(lambda value: f"{value:.3f}")
        top["Odds_ratio"] = top["Odds_ratio"].map(lambda value: f"{value:.2f}")
        ax = fig.add_axes([0.08, 0.16, 0.84, 0.25])
        ax.axis("off")
        table = ax.table(cellText=top.values, colLabels=["Modalité", "Coefficient log-odds", "Odds ratio"], loc="center", cellLoc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.35)
        _paragraph(
            fig,
            "Un odds ratio compare une modalité à la catégorie de référence, toutes choses égales par ailleurs. Il ne correspond pas directement à une variation en pourcentage de probabilité et ne doit pas recevoir une interprétation causale.",
            0.12,
            size=8.5,
        )
        pdf.savefig(fig)
        plt.close(fig)

        fig = _new_page("4. Segmentation K-Means", 5)
        k3 = cluster_evaluation.loc[cluster_evaluation["k"] == 3].iloc[0]
        _paragraph(
            fig,
            f"Pour k=3, l'inertie vaut {k3['Inertie']:.2f}, le score de silhouette {k3['Silhouette']:.3f} et l'indice de Davies-Bouldin {k3['Davies_Bouldin']:.3f}. Le choix de trois groupes est un compromis de lisibilité : les métriques ne prouvent pas qu'il existe exactement trois populations naturelles.",
            0.87,
        )
        profile_rows = []
        for cluster, row in cluster_profiles.iterrows():
            profile_rows.append(
                [
                    f"Segment {cluster}",
                    int(row["Effectif"]),
                    f"{row['Pourcentage']:.1f}%",
                    f"{row['Q4']:.2f}",
                    f"{row['Q18']:.2f}",
                    f"{row['Q21']:.2f}",
                    f"{row['Q23']:.2f}",
                    f"{row['Taux_interet_Q10']:.1f}%",
                ]
            )
        ax = fig.add_axes([0.05, 0.55, 0.90, 0.24])
        ax.axis("off")
        table = ax.table(
            cellText=profile_rows,
            colLabels=["Groupe", "n", "%", "Q4", "Q18", "Q21", "Q23", "Intérêt Q10"],
            loc="center",
            cellLoc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(7.5)
        table.scale(1, 1.45)
        _paragraph(
            fig,
            "Q4 est ordonnée de 1 (visites fréquentes) à 6 (visites rares). Q18 et Q21 sont des tranches ordonnées ; Q23 est un nombre de sports. Le taux Q10 est calculé après le clustering pour décrire les groupes et n'a pas servi à les former.",
            0.49,
        )
        _add_image(fig, figures_dir / "cluster_profiles.png", [0.10, 0.09, 0.80, 0.32])
        pdf.savefig(fig)
        plt.close(fig)

        fig = _new_page("5. Diagnostic du nombre de groupes", 6)
        _add_image(fig, figures_dir / "elbow_method.png", [0.06, 0.43, 0.88, 0.43])
        _paragraph(
            fig,
            "L'inertie diminue mécaniquement quand k augmente. La silhouette et Davies-Bouldin montrent que les groupes restent modérément séparés. Trois clusters sont conservés pour une lecture simple et cohérente avec l'objectif exploratoire, pas parce qu'ils représenteraient une vérité définitive sur la clientèle.",
            0.35,
        )
        _paragraph(
            fig,
            "Limite importante : K-Means suppose une distance euclidienne et des groupes approximativement compacts. Même standardisés, des codes de tranches ne garantissent pas des écarts réellement égaux entre modalités. Une analyse sur davantage de données pourrait comparer d'autres représentations ou méthodes adaptées aux données mixtes.",
            0.21,
        )
        pdf.savefig(fig)
        plt.close(fig)

        fig = _new_page("6. Limites et recommandations", 7)
        limitations = [
            "Échantillon limité à 225 questionnaires recueillis en 2002.",
            "Étude académique, sans validation sur une base externe ni suivi temporel.",
            "Réponses déclaratives pouvant comporter des biais de questionnaire.",
            "Sélection univariée et coefficients sensibles au faible effectif.",
            "Scores calculés pour toute la base avec le modèle ajusté sur le train ; seule la performance du test mesure la généralisation.",
            "Droits de redistribution du classeur non documentés dans les fichiers source.",
        ]
        y = 0.87
        for item in limitations:
            fig.text(0.10, y, "• " + fill(item, width=88), fontsize=10, va="top", linespacing=1.35)
            y -= 0.095
        _paragraph(
            fig,
            "Les résultats peuvent servir à formuler des hypothèses de ciblage : adapter le message aux profils observés et utiliser le score comme outil de priorisation à tester. Toute décision marketing devrait être évaluée par une expérimentation séparée avec des coûts et conversions réellement observés. Aucun ROI n'est estimé dans cette étude.",
            0.27,
        )
        _paragraph(
            fig,
            "Améliorations possibles : collecter davantage de données, valider le modèle sur une nouvelle période, comparer quelques modèles simples, calibrer les probabilités et étudier la stabilité des clusters.",
            0.13,
        )
        pdf.savefig(fig)
        plt.close(fig)
