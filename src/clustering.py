"""Segmentation exploratoire par K-Means sur des variables ordinales."""

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler


class CustomerSegmentation:
    """Standardise les variables puis construit une segmentation K-Means."""

    def __init__(
        self,
        df: pd.DataFrame,
        features: Sequence[str],
        random_state: int = 42,
    ) -> None:
        self.df = df.copy()
        self.features = list(features)
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.kmeans: KMeans | None = None
        self.X_scaled: np.ndarray | None = None
        self.labels_: np.ndarray | None = None
        self.metrics_: dict | None = None
        self.standardized_profiles_: pd.DataFrame | None = None

    def prepare_data(self) -> np.ndarray:
        """Valide puis standardise les variables de segmentation."""
        missing = set(self.features).difference(self.df.columns)
        if missing:
            raise ValueError(f"Variables de clustering absentes : {sorted(missing)}")
        if self.df[self.features].isna().any().any():
            raise ValueError("Les variables de clustering contiennent des valeurs manquantes.")
        if not all(pd.api.types.is_numeric_dtype(self.df[col]) for col in self.features):
            raise TypeError("K-Means nécessite ici des variables numériques ou ordinales codées.")

        self.X_scaled = self.scaler.fit_transform(self.df[self.features])
        return self.X_scaled

    def evaluate_k(self, max_k: int = 8) -> pd.DataFrame:
        """Compare inertie, silhouette et Davies-Bouldin pour k=2 à max_k."""
        if self.X_scaled is None:
            self.prepare_data()
        if max_k < 2 or max_k >= len(self.df):
            raise ValueError("max_k doit être compris entre 2 et n_observations - 1.")

        rows = []
        for k in range(2, max_k + 1):
            model = KMeans(
                n_clusters=k,
                random_state=self.random_state,
                n_init=20,
            )
            labels = model.fit_predict(self.X_scaled)
            rows.append(
                {
                    "k": k,
                    "Inertie": float(model.inertia_),
                    "Silhouette": float(silhouette_score(self.X_scaled, labels)),
                    "Davies_Bouldin": float(
                        davies_bouldin_score(self.X_scaled, labels)
                    ),
                }
            )
        return pd.DataFrame(rows)

    def fit(self, n_clusters: int = 3) -> np.ndarray:
        """Ajuste K-Means et ordonne les segments par fréquence de visite."""
        if self.X_scaled is None:
            self.prepare_data()
        self.kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=self.random_state,
            n_init=20,
        )
        raw_labels = self.kmeans.fit_predict(self.X_scaled)

        # Q4 est codée de 1 (visites fréquentes) à 6 (visites rares).
        # L'ordre rend les numéros de segments plus lisibles et reproductibles.
        q4_position = self.features.index("Q4")
        ordered_old_labels = np.argsort(self.kmeans.cluster_centers_[:, q4_position])
        label_mapping = {old: new for new, old in enumerate(ordered_old_labels)}
        self.labels_ = np.asarray([label_mapping[label] for label in raw_labels])
        self.df["Cluster"] = self.labels_

        self.metrics_ = {
            "silhouette": float(silhouette_score(self.X_scaled, raw_labels)),
            "davies_bouldin": float(
                davies_bouldin_score(self.X_scaled, raw_labels)
            ),
            "inertie": float(self.kmeans.inertia_),
        }

        scaled = pd.DataFrame(self.X_scaled, columns=self.features, index=self.df.index)
        scaled["Cluster"] = self.labels_
        self.standardized_profiles_ = scaled.groupby("Cluster")[self.features].mean()
        return self.labels_.copy()

    def describe_clusters(self, target: str = "Q10", positive_code: int = 1) -> pd.DataFrame:
        """Décrit les moyennes et l'intérêt observé après le clustering."""
        if self.labels_ is None:
            raise ValueError("Appelez fit() avant describe_clusters().")
        profiles = self.df.groupby("Cluster")[self.features].mean()
        profiles["Effectif"] = self.df.groupby("Cluster").size()
        profiles["Pourcentage"] = profiles["Effectif"] / len(self.df) * 100
        if target in self.df.columns:
            interest = self.df[target].eq(positive_code)
            profiles["Taux_interet_Q10"] = (
                self.df.assign(_interest=interest)
                .groupby("Cluster")["_interest"]
                .mean()
                * 100
            )
        return profiles

    @property
    def standardized_profiles(self) -> pd.DataFrame:
        if self.standardized_profiles_ is None:
            raise ValueError("Appelez fit() avant de demander les profils standardisés.")
        return self.standardized_profiles_.copy()
