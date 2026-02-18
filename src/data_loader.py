"""
Module de chargement et préparation des données
"""

import pandas as pd
import numpy as np
from typing import Tuple, List


class DataLoader:
    """Classe pour charger et préparer les données Intersport"""

    def __init__(self, file_path: str):
        """
        Initialise le loader avec le chemin du fichier

        Args:
            file_path: Chemin vers le fichier Excel des données
        """
        self.file_path = file_path
        self.df = None
        self.df_clean = None

    def load_data(self) -> pd.DataFrame:
        """
        Charge les données depuis le fichier Excel

        Returns:
            DataFrame pandas contenant les données
        """
        try:
            self.df = pd.read_excel(self.file_path)
            print(f"✓ Données chargées avec succès: {self.df.shape[0]} lignes, {self.df.shape[1]} colonnes")
            return self.df
        except Exception as e:
            print(f"✗ Erreur lors du chargement des données: {e}")
            raise

    def audit_data(self) -> dict:
        """
        Effectue un audit complet de la qualité des données

        Returns:
            Dictionnaire contenant les résultats de l'audit
        """
        if self.df is None:
            raise ValueError("Les données doivent d'abord être chargées avec load_data()")

        audit_results = {
            'shape': self.df.shape,
            'columns': list(self.df.columns),
            'dtypes': self.df.dtypes.to_dict(),
            'missing_values': self.df.isnull().sum().to_dict(),
            'duplicates': self.df.duplicated().sum(),
            'memory_usage': self.df.memory_usage(deep=True).sum() / 1024**2,  # MB
        }

        # Statistiques descriptives
        audit_results['statistics'] = self.df.describe().to_dict()

        # Vérification des valeurs uniques par colonne
        audit_results['unique_values'] = {
            col: self.df[col].nunique() for col in self.df.columns
        }

        # Distribution de la variable cible
        if 'Q10' in self.df.columns:
            audit_results['target_distribution'] = self.df['Q10'].value_counts().to_dict()

        return audit_results

    def print_audit_report(self, audit_results: dict):
        """
        Affiche un rapport d'audit formaté

        Args:
            audit_results: Résultats de l'audit
        """
        print("\n" + "="*70)
        print("RAPPORT D'AUDIT DES DONNÉES")
        print("="*70)

        print(f"\n📊 Dimensions: {audit_results['shape'][0]} lignes × {audit_results['shape'][1]} colonnes")
        print(f"💾 Utilisation mémoire: {audit_results['memory_usage']:.2f} MB")

        print(f"\n🔍 Doublons détectés: {audit_results['duplicates']}")

        # Valeurs manquantes
        missing = {k: v for k, v in audit_results['missing_values'].items() if v > 0}
        if missing:
            print(f"\n⚠️  Valeurs manquantes:")
            for col, count in missing.items():
                pct = (count / audit_results['shape'][0]) * 100
                print(f"   - {col}: {count} ({pct:.1f}%)")
        else:
            print("\n✓ Aucune valeur manquante détectée")

        # Distribution de la cible
        if 'target_distribution' in audit_results:
            print(f"\n🎯 Distribution de la variable cible (Q10):")
            total = sum(audit_results['target_distribution'].values())
            for key, count in audit_results['target_distribution'].items():
                pct = (count / total) * 100
                label = "Intéressé" if key == 1 else "Non intéressé"
                print(f"   - {label} ({key}): {count} ({pct:.1f}%)")

        print("\n" + "="*70 + "\n")

    def clean_data(self, remove_duplicates: bool = True) -> pd.DataFrame:
        """
        Nettoie les données (doublons, valeurs aberrantes, etc.)

        Args:
            remove_duplicates: Si True, supprime les doublons

        Returns:
            DataFrame nettoyé
        """
        if self.df is None:
            raise ValueError("Les données doivent d'abord être chargées avec load_data()")

        self.df_clean = self.df.copy()

        # Suppression des doublons
        if remove_duplicates:
            n_before = len(self.df_clean)
            self.df_clean = self.df_clean.drop_duplicates()
            n_after = len(self.df_clean)
            if n_before > n_after:
                print(f"✓ {n_before - n_after} doublons supprimés")

        # On pourrait ajouter d'autres nettoyages ici
        # (valeurs aberrantes, standardisation, etc.)

        return self.df_clean

    def get_feature_variables(self, exclude: List[str] = None) -> List[str]:
        """
        Retourne la liste des variables features (sans ID et cible)

        Args:
            exclude: Liste de variables à exclure en plus

        Returns:
            Liste des noms de colonnes features
        """
        if self.df is None:
            raise ValueError("Les données doivent d'abord être chargées")

        exclude_vars = ['obs', 'Q10']  # ID et cible par défaut

        if exclude:
            exclude_vars.extend(exclude)

        features = [col for col in self.df.columns if col not in exclude_vars]

        return features

    def prepare_modeling_data(self, features: List[str], target: str = 'Q10') -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prépare les données pour la modélisation

        Args:
            features: Liste des features à utiliser
            target: Nom de la variable cible

        Returns:
            Tuple (X, y) pour la modélisation
        """
        df = self.df_clean if self.df_clean is not None else self.df

        X = df[features].copy()
        y = df[target].copy()

        return X, y
