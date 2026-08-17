"""Pipeline supervisé de scoring par régression logistique."""

from collections.abc import Sequence
import warnings

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.feature_selection import CramersVSelector


class ScoringModel:
    """Entraîne et évalue un score d'intérêt sans utiliser le test au fit."""

    def __init__(
        self,
        df: pd.DataFrame,
        candidate_features: Sequence[str],
        target: str = "Q10",
        positive_code: int = 1,
        random_state: int = 42,
    ) -> None:
        self.df = df.copy()
        self.candidate_features = list(candidate_features)
        self.target = target
        self.positive_code = positive_code
        self.random_state = random_state
        self.pipeline: Pipeline | None = None
        self.X_train: pd.DataFrame | None = None
        self.X_test: pd.DataFrame | None = None
        self.y_train: pd.Series | None = None
        self.y_test: pd.Series | None = None

    def prepare_data(self, test_size: float = 0.30):
        """Réalise le split stratifié avant toute sélection ou transformation."""
        missing = set(self.candidate_features).union({self.target}).difference(self.df.columns)
        if missing:
            raise ValueError(f"Colonnes absentes pour le scoring : {sorted(missing)}")

        X = self.df[self.candidate_features].copy()
        y = self.df[self.target].eq(self.positive_code).astype(int)
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=self.random_state,
            stratify=y,
        )
        return self.X_train, self.X_test, self.y_train, self.y_test

    def fit(
        self,
        top_n: int = 7,
        cramer_threshold: float = 0.15,
        max_iter: int = 2_000,
    ) -> Pipeline:
        """Ajuste sélection, one-hot encoding et modèle sur le train uniquement."""
        if self.X_train is None:
            self.prepare_data()

        self.pipeline = self._build_pipeline(top_n, cramer_threshold, max_iter)
        self.pipeline.fit(self.X_train, self.y_train)
        return self.pipeline

    def _build_pipeline(self, top_n: int, threshold: float, max_iter: int) -> Pipeline:
        return Pipeline(
            steps=[
                ("selection", CramersVSelector(top_n=top_n, threshold=threshold)),
                (
                    "encodage",
                    OneHotEncoder(
                        drop="first",
                        handle_unknown="ignore",
                        sparse_output=False,
                    ),
                ),
                (
                    "modele",
                    LogisticRegression(
                        max_iter=max_iter,
                        random_state=self.random_state,
                    ),
                ),
            ]
        )

    def evaluate(self, cv_folds: int = 5) -> dict:
        """Évalue une fois le test et réalise la cross-validation sur le train.

        Le pipeline complet est réajusté dans chaque fold : la sélection par V de
        Cramer et l'encodage ne voient donc jamais le fold de validation.
        """
        if self.pipeline is None or self.X_test is None:
            raise ValueError("Appelez prepare_data() puis fit() avant evaluate().")

        y_pred = self.pipeline.predict(self.X_test)
        y_probability = self.pipeline.predict_proba(self.X_test)[:, 1]
        metrics = {
            "accuracy": float(accuracy_score(self.y_test, y_pred)),
            "roc_auc": float(roc_auc_score(self.y_test, y_probability)),
            "precision": float(precision_score(self.y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(self.y_test, y_pred, zero_division=0)),
            "f1_score": float(f1_score(self.y_test, y_pred, zero_division=0)),
            "confusion_matrix": confusion_matrix(self.y_test, y_pred),
            "test_predictions": y_pred,
            "test_probabilities": y_probability,
        }

        cv = StratifiedKFold(
            n_splits=cv_folds,
            shuffle=True,
            random_state=self.random_state,
        )
        with warnings.catch_warnings():
            # Une modalité rare peut être absente du train d'un fold. Elle est
            # correctement traitée comme inconnue par OneHotEncoder.
            warnings.filterwarnings(
                "ignore",
                message="Found unknown categories.*",
                category=UserWarning,
            )
            cv_results = cross_validate(
                self.pipeline,
                self.X_train,
                self.y_train,
                cv=cv,
                scoring={
                    "accuracy": "accuracy",
                    "roc_auc": "roc_auc",
                    "precision": "precision",
                    "recall": "recall",
                    "f1": "f1",
                },
                return_train_score=False,
            )
        for name in ("accuracy", "roc_auc", "precision", "recall", "f1"):
            values = cv_results[f"test_{name}"]
            metrics[f"cv_{name}_mean"] = float(values.mean())
            metrics[f"cv_{name}_std"] = float(values.std())
        return metrics

    @property
    def selected_features(self) -> list[str]:
        """Variables retenues lors de l'ajustement final sur tout le train."""
        self._check_fitted()
        return list(self.pipeline.named_steps["selection"].selected_features_)

    def get_selection_results(self) -> pd.DataFrame:
        """Résultats du V de Cramer calculés sur le train final uniquement."""
        self._check_fitted()
        return self.pipeline.named_steps["selection"].results_.copy()

    def get_feature_importance(self) -> pd.DataFrame:
        """Retourne coefficients log-odds et odds ratios par modalité."""
        self._check_fitted()
        encoder = self.pipeline.named_steps["encodage"]
        model = self.pipeline.named_steps["modele"]
        feature_names = encoder.get_feature_names_out(self.selected_features)
        coefficients = model.coef_[0]
        return (
            pd.DataFrame(
                {
                    "Modalite": feature_names,
                    "Coefficient_log_odds": coefficients,
                    "Odds_ratio": np.exp(coefficients),
                    "Coefficient_absolu": np.abs(coefficients),
                }
            )
            .sort_values("Coefficient_absolu", ascending=False)
            .reset_index(drop=True)
        )

    def predict_score(self, X: pd.DataFrame | None = None) -> pd.Series:
        """Calcule les probabilités prédites avec le pipeline ajusté sur le train."""
        self._check_fitted()
        data = self.df[self.candidate_features] if X is None else X
        scores = self.pipeline.predict_proba(data)[:, 1]
        return pd.Series(scores, index=data.index, name="Score_Propension")

    def predict(self, X: pd.DataFrame | None = None) -> pd.Series:
        """Retourne la classe prédite au seuil interne de 0,5."""
        self._check_fitted()
        data = self.df[self.candidate_features] if X is None else X
        predictions = self.pipeline.predict(data)
        return pd.Series(predictions, index=data.index, name="Prediction")

    def _check_fitted(self) -> None:
        if self.pipeline is None:
            raise ValueError("Le pipeline doit d'abord être entraîné.")
