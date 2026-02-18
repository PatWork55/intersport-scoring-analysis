"""
Module de modélisation prédictive (Scoring)
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score,
    roc_auc_score, roc_curve, precision_recall_curve
)
import statsmodels.api as sm
from typing import Tuple, Dict


class ScoringModel:
    """Classe pour le modèle de scoring (prédiction d'appétence)"""

    def __init__(self, df: pd.DataFrame, features: list, target: str = 'Q10'):
        """
        Initialise le modèle de scoring

        Args:
            df: DataFrame contenant les données
            features: Liste des features à utiliser
            target: Nom de la variable cible
        """
        self.df = df.copy()
        self.features = features
        self.target = target
        self.model = None
        self.statsmodels_result = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.feature_names = None

    def prepare_data(self, test_size: float = 0.3, encode_dummies: bool = True) -> Tuple:
        """
        Prépare les données pour la modélisation

        Args:
            test_size: Proportion de données pour le test
            encode_dummies: Si True, applique un encodage one-hot

        Returns:
            Tuple (X_train, X_test, y_train, y_test)
        """
        # Préparation de X et y
        X = self.df[self.features].copy()

        # Encodage de la cible: 1 (Oui) -> 1, 2 (Non) -> 0
        y = self.df[self.target].apply(lambda x: 1 if x == 1 else 0)

        # Encodage one-hot des variables catégorielles si demandé
        if encode_dummies:
            X = pd.get_dummies(X, columns=self.features, drop_first=True)
            self.feature_names = list(X.columns)
        else:
            self.feature_names = self.features

        # Division train/test
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        print(f"\n✓ Données préparées:")
        print(f"   • Train: {len(self.X_train)} observations")
        print(f"   • Test: {len(self.X_test)} observations")
        print(f"   • Features: {len(self.feature_names)} variables")
        print(f"   • Distribution cible (train): {self.y_train.value_counts().to_dict()}")

        return self.X_train, self.X_test, self.y_train, self.y_test

    def fit_sklearn_model(self, max_iter: int = 1000) -> LogisticRegression:
        """
        Entraîne un modèle de régression logistique avec scikit-learn

        Args:
            max_iter: Nombre maximum d'itérations

        Returns:
            Modèle entraîné
        """
        if self.X_train is None:
            self.prepare_data()

        self.model = LogisticRegression(max_iter=max_iter, random_state=42)
        self.model.fit(self.X_train, self.y_train)

        print("\n✓ Modèle scikit-learn entraîné avec succès")

        return self.model

    def fit_statsmodels(self) -> sm.Logit:
        """
        Entraîne un modèle avec statsmodels pour obtenir des statistiques détaillées

        Returns:
            Résultats du modèle statsmodels
        """
        # Préparation sans encoding one-hot (pour statsmodels)
        X = self.df[self.features].copy()
        y = self.df[self.target].apply(lambda x: 1 if x == 1 else 0)

        # Ajout de la constante
        X = sm.add_constant(X)

        # Entraînement
        logit_model = sm.Logit(y, X)
        self.statsmodels_result = logit_model.fit(disp=False)

        print("\n✓ Modèle statsmodels entraîné avec succès")

        return self.statsmodels_result

    def evaluate_model(self) -> Dict:
        """
        Évalue le modèle sur l'ensemble de test

        Returns:
            Dictionnaire contenant les métriques de performance
        """
        if self.model is None:
            raise ValueError("Le modèle doit d'abord être entraîné")

        # Prédictions
        y_pred = self.model.predict(self.X_test)
        y_pred_proba = self.model.predict_proba(self.X_test)[:, 1]

        # Calcul des métriques
        metrics = {
            'accuracy': accuracy_score(self.y_test, y_pred),
            'roc_auc': roc_auc_score(self.y_test, y_pred_proba),
            'confusion_matrix': confusion_matrix(self.y_test, y_pred),
            'classification_report': classification_report(self.y_test, y_pred, output_dict=True)
        }

        # Validation croisée
        cv_scores = cross_val_score(self.model, self.X_train, self.y_train, cv=5, scoring='roc_auc')
        metrics['cv_mean'] = cv_scores.mean()
        metrics['cv_std'] = cv_scores.std()

        return metrics

    def print_evaluation(self, metrics: Dict):
        """
        Affiche les résultats d'évaluation du modèle

        Args:
            metrics: Dictionnaire des métriques
        """
        print("\n" + "="*80)
        print("ÉVALUATION DU MODÈLE DE SCORING")
        print("="*80 + "\n")

        print(f"📊 Métriques de performance:")
        print(f"   • Accuracy (Précision globale): {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
        print(f"   • ROC AUC Score: {metrics['roc_auc']:.4f}")
        print(f"   • Validation croisée (5-fold): {metrics['cv_mean']:.4f} ± {metrics['cv_std']:.4f}")

        print(f"\n📈 Matrice de confusion:")
        cm = metrics['confusion_matrix']
        print(f"\n                Prédit: Non    Prédit: Oui")
        print(f"Réel: Non          {cm[0,0]:<14} {cm[0,1]:<14}")
        print(f"Réel: Oui          {cm[1,0]:<14} {cm[1,1]:<14}")

        # Calcul des taux
        tn, fp, fn, tp = cm.ravel()
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0

        print(f"\n   • Sensibilité (Taux de vrais positifs): {sensitivity:.4f}")
        print(f"   • Spécificité (Taux de vrais négatifs): {specificity:.4f}")

        print(f"\n📋 Rapport de classification détaillé:")
        report = metrics['classification_report']
        print(f"\n   Classe 0 (Non intéressé):")
        print(f"      - Precision: {report['0']['precision']:.4f}")
        print(f"      - Recall: {report['0']['recall']:.4f}")
        print(f"      - F1-Score: {report['0']['f1-score']:.4f}")

        print(f"\n   Classe 1 (Intéressé):")
        print(f"      - Precision: {report['1']['precision']:.4f}")
        print(f"      - Recall: {report['1']['recall']:.4f}")
        print(f"      - F1-Score: {report['1']['f1-score']:.4f}")

        print("\n" + "="*80 + "\n")

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Extrait l'importance des variables du modèle

        Returns:
            DataFrame avec les coefficients et leur importance
        """
        if self.model is None:
            raise ValueError("Le modèle doit d'abord être entraîné")

        # Extraction des coefficients
        coefficients = pd.DataFrame({
            'Feature': self.feature_names,
            'Coefficient': self.model.coef_[0],
            'Abs_Coefficient': np.abs(self.model.coef_[0])
        }).sort_values(by='Abs_Coefficient', ascending=False)

        return coefficients

    def print_feature_importance(self, top_n: int = 15):
        """
        Affiche l'importance des variables

        Args:
            top_n: Nombre de variables à afficher
        """
        importance = self.get_feature_importance()

        print("\n" + "="*80)
        print("IMPORTANCE DES VARIABLES")
        print("="*80 + "\n")

        print(f"Top {top_n} des variables les plus influentes:\n")
        print(importance.head(top_n).to_string(index=False))

        print("\n📊 Interprétation:")
        print("   • Coefficient > 0: Augmente la probabilité d'adhésion")
        print("   • Coefficient < 0: Diminue la probabilité d'adhésion")
        print("   • |Coefficient| élevé: Influence forte")

        print("\n" + "="*80 + "\n")

    def predict_score(self, X: pd.DataFrame = None) -> pd.Series:
        """
        Calcule le score de propension (probabilité d'adhésion)

        Args:
            X: Données à scorer (si None, utilise df original)

        Returns:
            Série avec les probabilités
        """
        if self.model is None:
            raise ValueError("Le modèle doit d'abord être entraîné")

        if X is None:
            # Préparation des données originales
            X = self.df[self.features].copy()
            X = pd.get_dummies(X, columns=self.features, drop_first=True)

            # Assurer que les colonnes correspondent
            for col in self.feature_names:
                if col not in X.columns:
                    X[col] = 0
            X = X[self.feature_names]

        # Prédiction des probabilités
        scores = self.model.predict_proba(X)[:, 1]

        return pd.Series(scores, index=X.index, name='Score_Propension')

    def get_statsmodels_summary(self) -> str:
        """
        Retourne le résumé statistique complet du modèle statsmodels

        Returns:
            Résumé au format texte
        """
        if self.statsmodels_result is None:
            self.fit_statsmodels()

        return str(self.statsmodels_result.summary())
