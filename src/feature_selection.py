"""Sélection univariée de variables catégorielles avec le V de Cramer."""

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.base import BaseEstimator, TransformerMixin


def cramers_v(contingency_table: pd.DataFrame | np.ndarray) -> tuple[float, float]:
    """Calcule le V de Cramer corrigé et la p-value du test du Chi².

    La correction de biais est utile ici car l'échantillon est petit. Cette
    mesure décrit une association entre variables catégorielles, pas un lien
    causal ni une méthode universelle de feature selection.
    """
    table = np.asarray(contingency_table)
    if table.ndim != 2 or min(table.shape) < 2 or table.sum() <= 1:
        return 0.0, 1.0

    chi2, p_value, _, _ = chi2_contingency(table)
    n = table.sum()
    rows, columns = table.shape
    phi2_corrected = max(
        0.0,
        chi2 / n - ((columns - 1) * (rows - 1)) / (n - 1),
    )
    rows_corrected = rows - ((rows - 1) ** 2) / (n - 1)
    columns_corrected = columns - ((columns - 1) ** 2) / (n - 1)
    denominator = min(rows_corrected - 1, columns_corrected - 1)
    value = np.sqrt(phi2_corrected / denominator) if denominator > 0 else 0.0
    return float(value), float(p_value)


class FeatureSelector:
    """Calcule et présente les associations entre plusieurs variables et une cible."""

    def __init__(self, df: pd.DataFrame, target: str) -> None:
        self.df = df
        self.target = target
        self.results_df: pd.DataFrame | None = None

    def compute_associations(self, features: Sequence[str]) -> pd.DataFrame:
        """Classe les variables par V de Cramer décroissant."""
        missing = set(features).union({self.target}).difference(self.df.columns)
        if missing:
            raise ValueError(f"Colonnes absentes pour la sélection : {sorted(missing)}")

        results = []
        for feature in features:
            table = pd.crosstab(self.df[feature], self.df[self.target], dropna=False)
            value, p_value = cramers_v(table)
            results.append(
                {
                    "Variable": feature,
                    "Cramer_V": value,
                    "P_Value": p_value,
                    "Significatif_5pct": bool(p_value < 0.05),
                    "Modalites_train": int(self.df[feature].nunique(dropna=False)),
                }
            )

        self.results_df = (
            pd.DataFrame(results)
            .sort_values("Cramer_V", ascending=False)
            .reset_index(drop=True)
        )
        return self.results_df.copy()

    def get_top_features(self, n: int, threshold: float) -> list[str]:
        """Retourne au plus ``n`` variables dépassant le seuil choisi."""
        if self.results_df is None:
            raise ValueError("Appelez compute_associations() avant get_top_features().")
        selected = self.results_df.loc[
            self.results_df["Cramer_V"] >= threshold, "Variable"
        ].head(n)
        if selected.empty:
            selected = self.results_df["Variable"].head(1)
        return selected.tolist()

    def check_multicollinearity(self, features: Sequence[str]) -> pd.DataFrame:
        """Calcule les V de Cramer deux à deux entre variables sélectionnées."""
        matrix = pd.DataFrame(1.0, index=features, columns=features)
        for i, first in enumerate(features):
            for second in features[i + 1 :]:
                value, _ = cramers_v(pd.crosstab(self.df[first], self.df[second]))
                matrix.loc[first, second] = value
                matrix.loc[second, first] = value
        return matrix


class CramersVSelector(BaseEstimator, TransformerMixin):
    """Transformer scikit-learn ajustant la sélection uniquement sur son train."""

    def __init__(self, top_n: int = 7, threshold: float = 0.15) -> None:
        self.top_n = top_n
        self.threshold = threshold

    def fit(self, X: pd.DataFrame, y: Sequence[int]):
        frame = self._as_frame(X)
        target_name = "__target__"
        selection_frame = frame.copy()
        selection_frame[target_name] = np.asarray(y)
        selector = FeatureSelector(selection_frame, target_name)
        self.results_ = selector.compute_associations(list(frame.columns))
        self.selected_features_ = selector.get_top_features(self.top_n, self.threshold)
        self.feature_names_in_ = np.asarray(frame.columns, dtype=object)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not hasattr(self, "selected_features_"):
            raise ValueError("Le sélecteur doit d'abord être ajusté.")
        frame = self._as_frame(X)
        missing = set(self.selected_features_).difference(frame.columns)
        if missing:
            raise ValueError(f"Variables sélectionnées absentes : {sorted(missing)}")
        return frame.loc[:, self.selected_features_]

    def get_feature_names_out(self, input_features=None) -> np.ndarray:
        return np.asarray(self.selected_features_, dtype=object)

    @staticmethod
    def _as_frame(X) -> pd.DataFrame:
        if not isinstance(X, pd.DataFrame):
            raise TypeError("CramersVSelector attend un DataFrame pandas.")
        return X
