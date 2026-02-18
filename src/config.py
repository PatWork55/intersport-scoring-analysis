"""
Configuration du projet d'analyse Intersport
"""

# Chemins des fichiers
DATA_FILE = 'donnees_isport.xls'
OUTPUT_DIR = 'resultats/'
FIGURES_DIR = 'resultats/figures/'

# Configuration de l'analyse
TARGET_VARIABLE = 'Q10'  # Variable cible: intérêt pour la carte de fidélité
ID_VARIABLE = 'obs'

# Variables potentiellement problématiques (data leakage)
LEAK_VARIABLES = ['Q11', 'Q13']  # Questions conditionnelles à Q10

# Configuration du clustering
N_CLUSTERS = 3
RANDOM_STATE = 42

# Configuration du modèle de scoring
TEST_SIZE = 0.3
MODEL_MAX_ITER = 1000

# Configuration des graphiques
FIGURE_DPI = 300
FIGURE_STYLE = 'whitegrid'
COLOR_PALETTE = 'viridis'

# Seuil de sélection des variables (Cramer's V)
CRAMER_V_THRESHOLD = 0.15

# Mapping des codes pour interprétation
MAPPINGS = {
    'Q10': {1: 'Oui (intéressé)', 2: 'Non (pas intéressé)'},
    'Q17': {1: 'Homme', 2: 'Femme'},
    'Q23': {1: 'Oui (club)', 2: 'Non (pas de club)', 0: 'Non renseigné'},
    # Ajouter d'autres mappings selon le besoin
}
