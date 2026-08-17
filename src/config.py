"""Configuration centrale de l'étude de cas."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "donnees_isport.xls"
OUTPUT_DIR = PROJECT_ROOT / "resultats"
FIGURES_DIR = OUTPUT_DIR / "figures"
REPORT_FILE = PROJECT_ROOT / "RAPPORT_COMPLET.pdf"

DATA_SHEET = "données"
TARGET_VARIABLE = "Q10"
TARGET_POSITIVE_CODE = 1
ID_VARIABLE = "obs"

# Q11 et Q13 sont conditionnelles à Q10. Q12a-e et Q14 portent directement
# sur la carte et sont écartées pour obtenir un score fondé sur le profil et le
# comportement du client, plutôt que sur des réponses très proches de la cible.
SCORING_EXCLUDED_VARIABLES = [
    ID_VARIABLE,
    TARGET_VARIABLE,
    "Q11",
    "Q12a",
    "Q12b",
    "Q12c",
    "Q12d",
    "Q12e",
    "Q13",
    "Q14",
]

# Variables dont le codage est ordinal ou quantitatif dans l'onglet « Codage ».
# Q4 : fréquence de visite (1 = très fréquent, 6 = rare)
# Q18 : tranche d'âge ; Q21 : budget sport annuel ; Q23 : nombre de sports.
CLUSTER_FEATURES = ["Q4", "Q18", "Q21", "Q23"]
N_CLUSTERS = 3
MAX_CLUSTERS = 8

RANDOM_STATE = 42
TEST_SIZE = 0.30
CV_FOLDS = 5
MODEL_MAX_ITER = 2_000
DECISION_THRESHOLD = 0.50

CRAMER_V_THRESHOLD = 0.15
TOP_N_FEATURES = 7

FEATURE_LABELS = {
    "Q1": "Achat effectué lors de la visite",
    "Q2": "Raison de non-achat",
    "Q3": "Motif de venue au magasin",
    "Q4": "Fréquence de visite du magasin",
    "Q5": "Achat antérieur dans le magasin",
    "Q6": "Fréquence d'achat lors des visites",
    "Q7": "Montant moyen dépensé",
    "Q18": "Tranche d'âge",
    "Q21": "Budget sport annuel",
    "Q22": "Catégorie socioprofessionnelle",
    "Q23": "Nombre de sports pratiqués",
}
