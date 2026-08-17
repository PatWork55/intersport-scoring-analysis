"""Visualisations sobres pour l'analyse et le rapport."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import roc_auc_score, roc_curve


class DataVisualizer:
    """Génère les figures PNG du projet."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        sns.set_theme(style="whitegrid", palette="colorblind")
        plt.rcParams.update(
            {
                "figure.dpi": 110,
                "savefig.dpi": 200,
                "font.size": 10,
                "axes.titlesize": 13,
                "axes.labelsize": 11,
            }
        )

    def _save(self, fig: plt.Figure, filename: str) -> plt.Figure:
        fig.tight_layout()
        fig.savefig(self.output_dir / filename, bbox_inches="tight")
        plt.close(fig)
        return fig

    def plot_target_distribution(self, df: pd.DataFrame, target: str) -> plt.Figure:
        counts = df[target].value_counts().sort_index()
        labels = ["Intéressé" if code == 1 else "Non intéressé" for code in counts.index]
        fig, ax = plt.subplots(figsize=(7, 4.5))
        bars = ax.bar(labels, counts.values, color=["#2a9d8f", "#e76f51"])
        ax.bar_label(bars, labels=[f"{n} ({n / counts.sum():.1%})" for n in counts])
        ax.set_ylabel("Nombre de répondants")
        ax.set_title("Intérêt déclaré pour une carte de fidélité (Q10)")
        ax.set_ylim(0, max(counts) * 1.18)
        return self._save(fig, "target_distribution.png")

    def plot_cramers_v(self, results: pd.DataFrame, top_n: int = 15) -> plt.Figure:
        data = results.head(top_n).sort_values("Cramer_V")
        fig, ax = plt.subplots(figsize=(9, 7))
        ax.barh(data["Variable"], data["Cramer_V"], color="#457b9d")
        ax.axvline(0.15, color="#e76f51", linestyle="--", label="Seuil retenu : 0,15")
        ax.set_xlabel("V de Cramer corrigé")
        ax.set_title("Association avec Q10 — calcul sur le train uniquement")
        ax.legend()
        return self._save(fig, "cramers_v_ranking.png")

    def plot_correlation_matrix(self, matrix: pd.DataFrame) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(8, 6.5))
        sns.heatmap(
            matrix,
            annot=True,
            fmt=".2f",
            cmap="Blues",
            vmin=0,
            vmax=1,
            square=True,
            ax=ax,
        )
        ax.set_title("V de Cramer entre variables sélectionnées (train)")
        return self._save(fig, "correlation_matrix.png")

    def plot_cluster_evaluation(self, evaluation: pd.DataFrame) -> plt.Figure:
        fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
        specifications = [
            ("Inertie", "Inertie", "plus faible"),
            ("Silhouette", "Score de silhouette", "plus élevé"),
            ("Davies_Bouldin", "Indice de Davies-Bouldin", "plus faible"),
        ]
        for ax, (column, title, direction) in zip(axes, specifications):
            ax.plot(evaluation["k"], evaluation[column], marker="o", color="#457b9d")
            ax.axvline(3, color="#e76f51", linestyle="--", alpha=0.9)
            ax.set_xlabel("Nombre de clusters k")
            ax.set_title(f"{title}\n({direction} = mieux)")
        return self._save(fig, "elbow_method.png")

    def plot_cluster_sizes(self, df: pd.DataFrame) -> plt.Figure:
        counts = df["Cluster"].value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(7, 4.5))
        bars = ax.bar([f"Segment {i}" for i in counts.index], counts.values, color="#2a9d8f")
        ax.bar_label(bars, labels=[f"{n} ({n / counts.sum():.1%})" for n in counts])
        ax.set_ylabel("Nombre de répondants")
        ax.set_title("Taille des segments K-Means")
        ax.set_ylim(0, max(counts) * 1.18)
        return self._save(fig, "cluster_sizes.png")

    def plot_cluster_profiles(self, standardized_profiles: pd.DataFrame) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(8, 5))
        data = standardized_profiles.rename(index=lambda value: f"Segment {value}")
        sns.heatmap(
            data.T,
            annot=True,
            fmt=".2f",
            cmap="vlag",
            center=0,
            linewidths=0.5,
            cbar_kws={"label": "Écart à la moyenne (z-score)"},
            ax=ax,
        )
        ax.set_title("Profils standardisés des segments")
        ax.set_xlabel("")
        ax.set_ylabel("Variables de segmentation")
        return self._save(fig, "cluster_profiles.png")

    def plot_confusion_matrix(self, matrix: np.ndarray) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(6, 5))
        sns.heatmap(
            matrix,
            annot=True,
            fmt="d",
            cmap="Blues",
            cbar=False,
            xticklabels=["Non", "Oui"],
            yticklabels=["Non", "Oui"],
            ax=ax,
        )
        ax.set_xlabel("Prédiction")
        ax.set_ylabel("Valeur observée")
        ax.set_title("Matrice de confusion — jeu de test")
        return self._save(fig, "confusion_matrix.png")

    def plot_roc_curve(self, y_true, probabilities) -> plt.Figure:
        false_positive_rate, true_positive_rate, _ = roc_curve(y_true, probabilities)
        auc = roc_auc_score(y_true, probabilities)
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(
            false_positive_rate,
            true_positive_rate,
            color="#e76f51",
            linewidth=2,
            label=f"Régression logistique (AUC = {auc:.3f})",
        )
        ax.plot([0, 1], [0, 1], linestyle="--", color="grey", label="Hasard")
        ax.set_xlabel("Taux de faux positifs")
        ax.set_ylabel("Taux de vrais positifs")
        ax.set_title("Courbe ROC — jeu de test indépendant")
        ax.legend(loc="lower right")
        return self._save(fig, "roc_curve.png")

    def plot_feature_importance(self, importance: pd.DataFrame, top_n: int = 15) -> plt.Figure:
        data = importance.head(top_n).sort_values("Coefficient_log_odds")
        colors = np.where(data["Coefficient_log_odds"] >= 0, "#2a9d8f", "#e76f51")
        fig, ax = plt.subplots(figsize=(9, 7))
        ax.barh(data["Modalite"], data["Coefficient_log_odds"], color=colors)
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set_xlabel("Coefficient de régression (log-odds)")
        ax.set_title("Modalités les plus associées à la prédiction")
        return self._save(fig, "feature_importance.png")

    def plot_score_distribution(self, scores: pd.Series) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(8, 4.8))
        ax.hist(scores, bins=20, color="#457b9d", edgecolor="white", alpha=0.9)
        ax.axvline(0.5, color="#e76f51", linestyle="--", label="Seuil de décision : 0,5")
        ax.axvline(scores.mean(), color="black", linestyle=":", label=f"Moyenne : {scores.mean():.3f}")
        ax.set_xlabel("Score de propension prédit")
        ax.set_ylabel("Nombre de répondants")
        ax.set_title("Distribution des scores produits par le modèle final")
        ax.legend()
        return self._save(fig, "score_distribution.png")
