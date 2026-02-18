"""
Module de segmentation client (Clustering K-Means)
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
from typing import Tuple, Dict


class CustomerSegmentation:
    """Classe pour la segmentation de clients avec K-Means"""

    def __init__(self, df: pd.DataFrame, features: list):
        """
        Initialise la segmentation

        Args:
            df: DataFrame contenant les données
            features: Liste des features à utiliser pour le clustering
        """
        self.df = df.copy()
        self.features = features
        self.scaler = StandardScaler()
        self.kmeans = None
        self.df_scaled = None
        self.cluster_labels = None

    def prepare_data(self) -> np.ndarray:
        """
        Prépare et standardise les données pour le clustering

        Returns:
            Données standardisées (numpy array)
        """
        # Sélection des features
        X = self.df[self.features].values

        # Standardisation (mean=0, std=1)
        X_scaled = self.scaler.fit_transform(X)

        self.df_scaled = X_scaled

        print(f"✓ Données préparées: {X_scaled.shape[0]} observations, {X_scaled.shape[1]} variables")
        print(f"✓ Standardisation appliquée (mean=0, std=1)")

        return X_scaled

    def find_optimal_clusters(self, max_k: int = 10) -> Dict:
        """
        Trouve le nombre optimal de clusters avec la méthode du coude

        Args:
            max_k: Nombre maximum de clusters à tester

        Returns:
            Dictionnaire avec les métriques pour chaque k
        """
        if self.df_scaled is None:
            self.prepare_data()

        results = {
            'k': [],
            'inertia': [],
            'silhouette': [],
            'davies_bouldin': []
        }

        print("\n🔍 Recherche du nombre optimal de clusters...")
        print(f"{'K':<5} {'Inertie':<15} {'Silhouette':<15} {'Davies-Bouldin':<15}")
        print("-" * 50)

        for k in range(2, max_k + 1):
            # Entraînement K-Means
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(self.df_scaled)

            # Calcul des métriques
            inertia = kmeans.inertia_
            silhouette = silhouette_score(self.df_scaled, labels)
            davies_bouldin = davies_bouldin_score(self.df_scaled, labels)

            results['k'].append(k)
            results['inertia'].append(inertia)
            results['silhouette'].append(silhouette)
            results['davies_bouldin'].append(davies_bouldin)

            print(f"{k:<5} {inertia:<15.2f} {silhouette:<15.3f} {davies_bouldin:<15.3f}")

        print("-" * 50)
        print("\n📊 Critères de sélection:")
        print("   • Inertie: Plus faible = mieux (mais attention au sur-ajustement)")
        print("   • Silhouette: Plus élevé = mieux (max = 1)")
        print("   • Davies-Bouldin: Plus faible = mieux (min = 0)")

        return results

    def fit_kmeans(self, n_clusters: int = 3) -> np.ndarray:
        """
        Entraîne le modèle K-Means avec un nombre de clusters spécifié

        Args:
            n_clusters: Nombre de clusters souhaité

        Returns:
            Labels des clusters pour chaque observation
        """
        if self.df_scaled is None:
            self.prepare_data()

        # Entraînement du modèle
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.cluster_labels = self.kmeans.fit_predict(self.df_scaled)

        # Ajout des labels au DataFrame original
        self.df['Cluster'] = self.cluster_labels

        print(f"\n✓ K-Means entraîné avec {n_clusters} clusters")
        print(f"\n📊 Distribution des clusters:")
        print(self.df['Cluster'].value_counts().sort_index())

        # Métriques de qualité
        silhouette = silhouette_score(self.df_scaled, self.cluster_labels)
        davies_bouldin = davies_bouldin_score(self.df_scaled, self.cluster_labels)

        print(f"\n📈 Qualité du clustering:")
        print(f"   • Silhouette Score: {silhouette:.3f}")
        print(f"   • Davies-Bouldin Index: {davies_bouldin:.3f}")

        return self.cluster_labels

    def describe_clusters(self) -> pd.DataFrame:
        """
        Caractérise chaque cluster (moyennes des variables)

        Returns:
            DataFrame avec les statistiques de chaque cluster
        """
        if self.cluster_labels is None:
            raise ValueError("Vous devez d'abord entraîner le modèle avec fit_kmeans()")

        # Calcul des moyennes par cluster
        cluster_profiles = self.df.groupby('Cluster')[self.features].mean()

        # Calcul des effectifs
        cluster_sizes = self.df['Cluster'].value_counts().sort_index()
        cluster_profiles['Effectif'] = cluster_sizes

        # Calcul du pourcentage
        cluster_profiles['Pourcentage'] = (cluster_profiles['Effectif'] / len(self.df) * 100).round(2)

        print("\n" + "="*80)
        print("PROFILS DES CLUSTERS")
        print("="*80 + "\n")
        print(cluster_profiles.to_string())
        print("\n" + "="*80 + "\n")

        return cluster_profiles

    def analyze_target_by_cluster(self, target: str = 'Q10') -> pd.DataFrame:
        """
        Analyse la distribution de la variable cible par cluster

        Args:
            target: Nom de la variable cible

        Returns:
            Table croisée cluster × cible
        """
        if self.cluster_labels is None:
            raise ValueError("Vous devez d'abord entraîner le modèle avec fit_kmeans()")

        # Table de contingence
        crosstab = pd.crosstab(
            self.df['Cluster'],
            self.df[target],
            normalize='index'
        ) * 100  # Pourcentages

        print("\n" + "="*80)
        print(f"DISTRIBUTION DE {target} PAR CLUSTER (en %)")
        print("="*80 + "\n")
        print(crosstab.round(2).to_string())
        print("\n" + "="*80 + "\n")

        return crosstab

    def get_cluster_interpretation(self, target: str = 'Q10') -> Dict[int, str]:
        """
        Génère une interprétation automatique de chaque cluster

        Args:
            target: Variable cible

        Returns:
            Dictionnaire {cluster_id: description}
        """
        if self.cluster_labels is None:
            raise ValueError("Vous devez d'abord entraîner le modèle")

        profiles = self.describe_clusters()
        target_dist = self.analyze_target_by_cluster(target)

        interpretations = {}

        for cluster_id in profiles.index:
            # Calcul du taux d'intérêt pour la carte
            if 1 in target_dist.columns:
                interest_rate = target_dist.loc[cluster_id, 1]
            else:
                interest_rate = 0

            size = profiles.loc[cluster_id, 'Effectif']
            pct = profiles.loc[cluster_id, 'Pourcentage']

            # Classification basée sur le taux d'intérêt
            if interest_rate > 70:
                category = "Ambassadeurs"
            elif interest_rate > 40:
                category = "Potentiel"
            else:
                category = "Réfractaires"

            interpretations[cluster_id] = {
                'Catégorie': category,
                'Taux_Interet': f"{interest_rate:.1f}%",
                'Effectif': int(size),
                'Pourcentage': f"{pct:.1f}%"
            }

        return interpretations
