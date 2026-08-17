"""Chargement, validation et nettoyage léger des données."""

from pathlib import Path
from typing import Iterable

import pandas as pd


class DataLoader:
    """Charge le questionnaire et applique des contrôles reproductibles."""

    def __init__(self, file_path: str | Path, sheet_name: str = "données") -> None:
        self.file_path = Path(file_path)
        self.sheet_name = sheet_name
        self.df: pd.DataFrame | None = None
        self.df_clean: pd.DataFrame | None = None

    def load_data(self) -> pd.DataFrame:
        """Charge l'onglet de données du classeur Excel."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Fichier de données introuvable : {self.file_path}")

        self.df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)
        self._validate_schema(self.df)
        return self.df.copy()

    @staticmethod
    def _validate_schema(df: pd.DataFrame) -> None:
        required = {"obs", "Q10"}
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"Colonnes obligatoires absentes : {sorted(missing)}")
        if not set(df["Q10"].dropna().unique()).issubset({1, 2}):
            raise ValueError("Q10 doit contenir uniquement les codes 1 (oui) et 2 (non).")

    def audit_data(self) -> dict:
        """Retourne les principaux contrôles de qualité du jeu de données."""
        if self.df is None:
            raise ValueError("Appelez load_data() avant audit_data().")

        return {
            "shape": self.df.shape,
            "duplicates": int(self.df.duplicated().sum()),
            "missing_values": int(self.df.isna().sum().sum()),
            "target_distribution": self.df["Q10"].value_counts().sort_index().to_dict(),
            "object_columns": list(self.df.select_dtypes(include="object").columns),
        }

    def clean_data(self, remove_duplicates: bool = True) -> pd.DataFrame:
        """Supprime les doublons exacts et réinitialise l'index."""
        if self.df is None:
            raise ValueError("Appelez load_data() avant clean_data().")

        cleaned = self.df.copy()
        if remove_duplicates:
            cleaned = cleaned.drop_duplicates()
        self.df_clean = cleaned.reset_index(drop=True)
        return self.df_clean.copy()

    def get_feature_variables(self, exclude: Iterable[str] | None = None) -> list[str]:
        """Liste les variables disponibles en excluant les colonnes indiquées."""
        df = self.df_clean if self.df_clean is not None else self.df
        if df is None:
            raise ValueError("Les données doivent d'abord être chargées.")
        excluded = set(exclude or [])
        return [column for column in df.columns if column not in excluded]
