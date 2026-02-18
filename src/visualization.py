"""
Module de visualisation des résultats
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, precision_recall_curve, roc_auc_score
from typing import List, Tuple
import os


class DataVisualizer:
    """Classe pour créer toutes les visualisations du projet"""

    def __init__(self, output_dir: str = 'resultats/figures/'):
        """
        Initialise le visualiseur

        Args:
            output_dir: Répertoire de sortie pour les figures
        """
        self.output_dir = output_dir
        self.setup_style()

        # Créer le répertoire s'il n'existe pas
        os.makedirs(output_dir, exist_ok=True)

    @staticmethod
    def setup_style():
        """Configure le style des graphiques"""
        sns.set_theme(style="whitegrid")
        plt.rcParams['figure.dpi'] = 100
        plt.rcParams['savefig.dpi'] = 300
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 11
        plt.rcParams['axes.titlesize'] = 13
        plt.rcParams['xtick.labelsize'] = 9
        plt.rcParams['ytick.labelsize'] = 9
        plt.rcParams['legend.fontsize'] = 9
        plt.rcParams['figure.titlesize'] = 14

    def plot_target_distribution(self, df: pd.DataFrame, target: str = 'Q10',
                                 save: bool = True) -> plt.Figure:
        """
        Graphique de distribution de la variable cible

        Args:
            df: DataFrame
            target: Variable cible
            save: Si True, sauvegarde le graphique

        Returns:
            Figure matplotlib
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Pie chart
        counts = df[target].value_counts().sort_index()
        labels = ['Oui (Intéressé)' if x == 1 else 'Non (Pas intéressé)' for x in counts.index]
        colors = ['#2ecc71', '#e74c3c']

        ax1.pie(counts.values, labels=labels, autopct='%1.1f%%',
                colors=colors, startangle=90, explode=(0.05, 0))
        ax1.set_title(f'Distribution de {target}\n(Intérêt pour la carte de fidélité)')

        # Bar chart
        ax2.bar(labels, counts.values, color=colors, alpha=0.7, edgecolor='black')
        ax2.set_ylabel('Nombre de clients')
        ax2.set_title('Effectifs par modalité')
        ax2.grid(axis='y', alpha=0.3)

        for i, v in enumerate(counts.values):
            ax2.text(i, v + 2, str(v), ha='center', fontweight='bold')

        plt.tight_layout()

        if save:
            plt.savefig(os.path.join(self.output_dir, 'target_distribution.png'),
                       bbox_inches='tight')
            print(f"✓ Graphique sauvegardé: target_distribution.png")

        return fig

    def plot_cramers_v(self, results_df: pd.DataFrame, top_n: int = 15,
                       save: bool = True) -> plt.Figure:
        """
        Graphique en barres du V de Cramer

        Args:
            results_df: DataFrame des résultats de sélection
            top_n: Nombre de variables à afficher
            save: Si True, sauvegarde le graphique

        Returns:
            Figure matplotlib
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        data = results_df.head(top_n).copy()
        colors = ['green' if p < 0.05 else 'orange' for p in data['P_Value']]

        ax.barh(data['Variable'], data['Cramer_V'], color=colors, alpha=0.7, edgecolor='black')
        ax.set_xlabel("V de Cramer (force de l'association)")
        ax.set_title(f"Top {top_n} - Variables les plus associées à Q10\n(Vert = significatif p<0.05)")
        ax.invert_yaxis()
        ax.grid(axis='x', alpha=0.3)

        # Lignes de référence
        ax.axvline(0.1, color='gray', linestyle='--', alpha=0.5, label='Faible (0.1)')
        ax.axvline(0.2, color='gray', linestyle='--', alpha=0.7, label='Modéré (0.2)')
        ax.legend()

        plt.tight_layout()

        if save:
            plt.savefig(os.path.join(self.output_dir, 'cramers_v_ranking.png'),
                       bbox_inches='tight')
            print(f"✓ Graphique sauvegardé: cramers_v_ranking.png")

        return fig

    def plot_correlation_matrix(self, corr_matrix: pd.DataFrame,
                               save: bool = True) -> plt.Figure:
        """
        Heatmap de corrélation entre variables

        Args:
            corr_matrix: Matrice de corrélation
            save: Si True, sauvegarde le graphique

        Returns:
            Figure matplotlib
        """
        fig, ax = plt.subplots(figsize=(12, 10))

        sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
                   center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                   vmin=0, vmax=1, ax=ax)

        ax.set_title('Matrice de corrélation (V de Cramer)\nentre les variables sélectionnées')

        plt.tight_layout()

        if save:
            plt.savefig(os.path.join(self.output_dir, 'correlation_matrix.png'),
                       bbox_inches='tight')
            print(f"✓ Graphique sauvegardé: correlation_matrix.png")

        return fig

    def plot_elbow_method(self, results: dict, save: bool = True) -> plt.Figure:
        """
        Graphique de la méthode du coude pour K-Means

        Args:
            results: Dictionnaire avec métriques pour chaque k
            save: Si True, sauvegarde le graphique

        Returns:
            Figure matplotlib
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))

        # Inertie
        axes[0].plot(results['k'], results['inertia'], 'bo-', linewidth=2, markersize=8)
        axes[0].set_xlabel('Nombre de clusters (k)')
        axes[0].set_ylabel('Inertie')
        axes[0].set_title('Méthode du Coude\n(chercher le "coude")')
        axes[0].grid(True, alpha=0.3)

        # Silhouette
        axes[1].plot(results['k'], results['silhouette'], 'go-', linewidth=2, markersize=8)
        axes[1].set_xlabel('Nombre de clusters (k)')
        axes[1].set_ylabel('Score de Silhouette')
        axes[1].set_title('Score de Silhouette\n(plus élevé = mieux)')
        axes[1].grid(True, alpha=0.3)

        # Davies-Bouldin
        axes[2].plot(results['k'], results['davies_bouldin'], 'ro-', linewidth=2, markersize=8)
        axes[2].set_xlabel('Nombre de clusters (k)')
        axes[2].set_ylabel('Index Davies-Bouldin')
        axes[2].set_title('Index Davies-Bouldin\n(plus faible = mieux)')
        axes[2].grid(True, alpha=0.3)

        plt.tight_layout()

        if save:
            plt.savefig(os.path.join(self.output_dir, 'elbow_method.png'),
                       bbox_inches='tight')
            print(f"✓ Graphique sauvegardé: elbow_method.png")

        return fig

    def plot_cluster_profiles(self, cluster_profiles: pd.DataFrame,
                             save: bool = True) -> plt.Figure:
        """
        Heatmap des profils de clusters

        Args:
            cluster_profiles: DataFrame avec moyennes par cluster
            save: Si True, sauvegarde le graphique

        Returns:
            Figure matplotlib
        """
        # Exclure les colonnes Effectif et Pourcentage
        data = cluster_profiles.drop(['Effectif', 'Pourcentage'], axis=1, errors='ignore')

        # Normalisation pour visualisation
        data_normalized = (data - data.min()) / (data.max() - data.min())

        fig, ax = plt.subplots(figsize=(14, 6))

        sns.heatmap(data_normalized.T, annot=data.T, fmt='.2f',
                   cmap='YlGnBu', cbar_kws={'label': 'Valeur normalisée'},
                   linewidths=1, ax=ax)

        ax.set_xlabel('Cluster')
        ax.set_ylabel('Variables')
        ax.set_title('Profils des Clusters\n(valeurs moyennes par groupe)')

        plt.tight_layout()

        if save:
            plt.savefig(os.path.join(self.output_dir, 'cluster_profiles.png'),
                       bbox_inches='tight')
            print(f"✓ Graphique sauvegardé: cluster_profiles.png")

        return fig

    def plot_cluster_sizes(self, df: pd.DataFrame, save: bool = True) -> plt.Figure:
        """
        Graphique de la taille des clusters

        Args:
            df: DataFrame avec colonne 'Cluster'
            save: Si True, sauvegarde le graphique

        Returns:
            Figure matplotlib
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        counts = df['Cluster'].value_counts().sort_index()
        colors = plt.cm.viridis(np.linspace(0, 1, len(counts)))

        # Bar chart
        ax1.bar(counts.index, counts.values, color=colors, alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Cluster')
        ax1.set_ylabel('Nombre de clients')
        ax1.set_title('Distribution des clients par cluster')
        ax1.grid(axis='y', alpha=0.3)

        for i, v in enumerate(counts.values):
            ax1.text(counts.index[i], v + 2, str(v), ha='center', fontweight='bold')

        # Pie chart
        ax2.pie(counts.values, labels=[f'Cluster {i}' for i in counts.index],
               autopct='%1.1f%%', colors=colors, startangle=90)
        ax2.set_title('Proportions des clusters')

        plt.tight_layout()

        if save:
            plt.savefig(os.path.join(self.output_dir, 'cluster_sizes.png'),
                       bbox_inches='tight')
            print(f"✓ Graphique sauvegardé: cluster_sizes.png")

        return fig

    def plot_confusion_matrix(self, cm: np.ndarray, save: bool = True) -> plt.Figure:
        """
        Heatmap de la matrice de confusion

        Args:
            cm: Matrice de confusion
            save: Si True, sauvegarde le graphique

        Returns:
            Figure matplotlib
        """
        fig, ax = plt.subplots(figsize=(8, 6))

        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=True,
                   xticklabels=['Non', 'Oui'],
                   yticklabels=['Non', 'Oui'], ax=ax)

        ax.set_ylabel('Valeur réelle')
        ax.set_xlabel('Valeur prédite')
        ax.set_title('Matrice de Confusion\n(Performance du modèle de scoring)')

        # Annotations supplémentaires
        tn, fp, fn, tp = cm.ravel()
        accuracy = (tp + tn) / (tp + tn + fp + fn)
        ax.text(0.5, -0.15, f'Accuracy: {accuracy:.2%}',
               ha='center', transform=ax.transAxes, fontsize=12, fontweight='bold')

        plt.tight_layout()

        if save:
            plt.savefig(os.path.join(self.output_dir, 'confusion_matrix.png'),
                       bbox_inches='tight')
            print(f"✓ Graphique sauvegardé: confusion_matrix.png")

        return fig

    def plot_roc_curve(self, y_true, y_pred_proba, save: bool = True) -> plt.Figure:
        """
        Courbe ROC

        Args:
            y_true: Vraies valeurs
            y_pred_proba: Probabilités prédites
            save: Si True, sauvegarde le graphique

        Returns:
            Figure matplotlib
        """
        fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
        auc_score = roc_auc_score(y_true, y_pred_proba)

        fig, ax = plt.subplots(figsize=(8, 8))

        ax.plot(fpr, tpr, color='darkorange', lw=2,
               label=f'ROC curve (AUC = {auc_score:.3f})')
        ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Hasard')

        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('Taux de Faux Positifs (1 - Spécificité)')
        ax.set_ylabel('Taux de Vrais Positifs (Sensibilité)')
        ax.set_title('Courbe ROC\n(Receiver Operating Characteristic)')
        ax.legend(loc="lower right")
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save:
            plt.savefig(os.path.join(self.output_dir, 'roc_curve.png'),
                       bbox_inches='tight')
            print(f"✓ Graphique sauvegardé: roc_curve.png")

        return fig

    def plot_feature_importance(self, importance_df: pd.DataFrame, top_n: int = 15,
                               save: bool = True) -> plt.Figure:
        """
        Graphique de l'importance des variables

        Args:
            importance_df: DataFrame avec colonnes Feature et Coefficient
            top_n: Nombre de features à afficher
            save: Si True, sauvegarde le graphique

        Returns:
            Figure matplotlib
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        data = importance_df.head(top_n)
        colors = ['green' if c > 0 else 'red' for c in data['Coefficient']]

        ax.barh(data['Feature'], data['Coefficient'], color=colors, alpha=0.7, edgecolor='black')
        ax.set_xlabel('Coefficient (impact sur la décision)')
        ax.set_title(f'Top {top_n} - Variables les plus influentes\n(Vert = favorable, Rouge = défavorable)')
        ax.invert_yaxis()
        ax.axvline(0, color='black', linewidth=0.8)
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()

        if save:
            plt.savefig(os.path.join(self.output_dir, 'feature_importance.png'),
                       bbox_inches='tight')
            print(f"✓ Graphique sauvegardé: feature_importance.png")

        return fig

    def plot_score_distribution(self, scores: pd.Series, save: bool = True) -> plt.Figure:
        """
        Distribution des scores de propension

        Args:
            scores: Série avec les scores
            save: Si True, sauvegarde le graphique

        Returns:
            Figure matplotlib
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Histogramme
        ax1.hist(scores, bins=30, color='skyblue', alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Score de propension')
        ax1.set_ylabel('Fréquence')
        ax1.set_title('Distribution des scores de propension')
        ax1.axvline(scores.mean(), color='red', linestyle='--', linewidth=2, label=f'Moyenne: {scores.mean():.3f}')
        ax1.axvline(0.5, color='green', linestyle='--', linewidth=2, label='Seuil: 0.5')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)

        # Boxplot
        ax2.boxplot(scores, vert=True)
        ax2.set_ylabel('Score de propension')
        ax2.set_title('Boxplot des scores')
        ax2.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        if save:
            plt.savefig(os.path.join(self.output_dir, 'score_distribution.png'),
                       bbox_inches='tight')
            print(f"✓ Graphique sauvegardé: score_distribution.png")

        return fig
