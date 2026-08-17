"""Tests ciblés des briques méthodologiques principales."""

import unittest

import numpy as np
import pandas as pd

from src.clustering import CustomerSegmentation
from src.data_loader import DataLoader
from src.feature_selection import CramersVSelector, cramers_v


class FeatureSelectionTests(unittest.TestCase):
    def test_cramers_v_is_high_for_perfect_association(self):
        value, p_value = cramers_v(np.array([[30, 0], [0, 30]]))
        # La correction de biais ramène légèrement le résultat sous 1.
        self.assertGreater(value, 0.95)
        self.assertLess(p_value, 0.05)

    def test_cramers_v_is_zero_for_independent_table(self):
        value, _ = cramers_v(np.array([[25, 25], [25, 25]]))
        self.assertAlmostEqual(value, 0.0)

    def test_selector_preserves_rows_and_limits_columns(self):
        X = pd.DataFrame(
            {
                "signal": [1, 1, 1, 2, 2, 2],
                "bruit": [1, 2, 1, 2, 1, 2],
            }
        )
        y = pd.Series([1, 1, 1, 0, 0, 0])
        selector = CramersVSelector(top_n=1, threshold=0.0).fit(X, y)
        transformed = selector.transform(X)
        self.assertEqual(transformed.shape, (6, 1))
        self.assertEqual(selector.selected_features_, ["signal"])


class DataPreparationTests(unittest.TestCase):
    def test_clean_data_removes_exact_duplicates(self):
        loader = DataLoader("fichier_inutilise.xls")
        loader.df = pd.DataFrame(
            {"obs": [1, 1, 2], "Q10": [1, 1, 2], "Q4": [2, 2, 4]}
        )
        cleaned = loader.clean_data()
        self.assertEqual(cleaned.shape, (2, 3))
        self.assertListEqual(cleaned["obs"].tolist(), [1, 2])

    def test_clustering_returns_one_label_per_row(self):
        df = pd.DataFrame(
            {
                "Q4": [1, 1, 2, 4, 5, 6],
                "Q18": [1, 2, 2, 4, 4, 5],
                "Q21": [3, 4, 3, 1, 1, 2],
                "Q23": [3, 4, 3, 0, 1, 0],
                "Q10": [1, 1, 1, 2, 2, 2],
            }
        )
        segmentation = CustomerSegmentation(df, ["Q4", "Q18", "Q21", "Q23"])
        labels = segmentation.fit(n_clusters=2)
        self.assertEqual(labels.shape, (len(df),))
        self.assertSetEqual(set(labels), {0, 1})


if __name__ == "__main__":
    unittest.main()
