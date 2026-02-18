"""
Module de sélection de variables avec le V de Cramer
"""

import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency
from typing import List, Tuple


class FeatureSelector:
    """Classe pour la sélection de variables avec des tests statistiques"""

    def __init__(self, df: pd.DataFrame, target: str):
        """
        Initialise le sélecteur

        Args:
            df: DataFrame contenant les données
            target: Nom de la variable cible
        """
        self.df = df
        self.target = target
        self.results_df = None

    @staticmethod
    def cramers_v(confusion_matrix: pd.DataFrame) -> float:
        """
        Calcule le V de Cramer (mesure d'association pour variables catégorielles)

        Le V de Cramer varie entre 0 (aucune association) et 1 (association parfaite)

        Args:
            confusion_matrix: Table de contingence entre deux variables

        Returns:
            Valeur du V de Cramer (entre 0 et 1)
        """
        chi2, p_value, dof, expected = chi2_contingency(confusion_matrix)

        n = confusion_matrix.sum().sum()  # Nombre total d'observations
        phi2 = chi2 / n  # Phi carré

        r, k = confusion_matrix.shape  # Nombre de lignes et colonnes

        # Correction de biais pour petits échantillons
        phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
        rcorr = r - ((r - 1) ** 2) / (n - 1)
        kcorr = k - ((k - 1) ** 2) / (n - 1)

        # Calcul du V de Cramer corrigé
        if min((kcorr - 1), (rcorr - 1)) > 0:
            v = np.sqrt(phi2corr / min((kcorr - 1), (rcorr - 1)))
        else:
            v = 0.0

        return v, p_value

    def compute_associations(self, features: List[str]) -> pd.DataFrame:
        """
        Calcule le V de Cramer entre chaque feature et la cible

        Args:
            features: Liste des features à tester

        Returns:
            DataFrame avec les résultats triés par V de Cramer décroissant
        """
        results = []

        for feature in features:
            try:
                # Création de la table de contingence
                contingency_table = pd.crosstab(self.df[feature], self.df[self.target])

                # Calcul du V de Cramer et p-value
                v, p_value = self.cramers_v(contingency_table)

                # Stockage des résultats
                results.append({
                    'Variable': feature,
                    'Cramer_V': v,
                    'P_Value': p_value,
                    'Significant': p_value < 0.05,
                    'Modalites': self.df[feature].nunique()
                })

            except Exception as e:
                print(f"Erreur pour la variable {feature}: {e}")
                continue

        # Création du DataFrame et tri par V de Cramer
        self.results_df = pd.DataFrame(results).sort_values(
            by='Cramer_V',
            ascending=False
        ).reset_index(drop=True)

        return self.results_df

    def get_top_features(self, n: int = 10, threshold: float = None) -> List[str]:
        """
        Retourne les n meilleures features ou celles au-dessus d'un seuil

        Args:
            n: Nombre de features à retourner
            threshold: Seuil minimum de V de Cramer (optionnel)

        Returns:
            Liste des noms de features sélectionnées
        """
        if self.results_df is None:
            raise ValueError("Vous devez d'abord calculer les associations avec compute_associations()")

        df_filtered = self.results_df.copy()

        # Filtrage par seuil si spécifié
        if threshold is not None:
            df_filtered = df_filtered[df_filtered['Cramer_V'] >= threshold]

        # Sélection des n meilleures
        top_features = df_filtered.head(n)['Variable'].tolist()

        return top_features

    def print_results(self, n: int = 15):
        """
        Affiche les résultats de sélection de variables

        Args:
            n: Nombre de variables à afficher
        """
        if self.results_df is None:
            raise ValueError("Aucun résultat disponible")

        print("\n" + "="*80)
        print("RÉSULTATS DE LA SÉLECTION DE VARIABLES (V de Cramer)")
        print("="*80 + "\n")

        print(f"Top {n} des variables les plus associées à {self.target}:\n")

        # Formatage de l'affichage
        display_df = self.results_df.head(n).copy()
        display_df['Cramer_V'] = display_df['Cramer_V'].apply(lambda x: f"{x:.4f}")
        display_df['P_Value'] = display_df['P_Value'].apply(lambda x: f"{x:.4e}" if x < 0.001 else f"{x:.4f}")
        display_df['Significant'] = display_df['Significant'].apply(lambda x: "✓" if x else "✗")

        print(display_df.to_string(index=True))

        print("\n" + "="*80)

        # Interprétation du V de Cramer
        print("\n📊 Interprétation du V de Cramer:")
        print("   • 0.00 - 0.10: Association négligeable")
        print("   • 0.10 - 0.20: Association faible")
        print("   • 0.20 - 0.40: Association modérée")
        print("   • 0.40 - 0.60: Association forte")
        print("   • 0.60 - 1.00: Association très forte")
        print("\n" + "="*80 + "\n")

    def check_multicollinearity(self, features: List[str]) -> pd.DataFrame:
        """
        Vérifie la multicolinéarité entre les features sélectionnées

        Args:
            features: Liste des features à vérifier

        Returns:
            Matrice de corrélation (V de Cramer entre features)
        """
        n_features = len(features)
        corr_matrix = np.zeros((n_features, n_features))

        for i, feat1 in enumerate(features):
            for j, feat2 in enumerate(features):
                if i == j:
                    corr_matrix[i, j] = 1.0
                elif i > j:
                    # Symétrie de la matrice
                    corr_matrix[i, j] = corr_matrix[j, i]
                else:
                    # Calcul du V de Cramer entre les deux features
                    contingency_table = pd.crosstab(self.df[feat1], self.df[feat2])
                    v, _ = self.cramers_v(contingency_table)
                    corr_matrix[i, j] = v

        # Conversion en DataFrame
        corr_df = pd.DataFrame(
            corr_matrix,
            index=features,
            columns=features
        )

        return corr_df
