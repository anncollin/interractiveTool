from pathlib import Path

#######################################################################################################
# PROJECT PATHS
# ----------------------------------------------------------------------------------------------------
# All paths are defined relative to the folder containing this config.py file.
# This avoids hard-coded absolute paths such as /home/anncollin/... and makes the tool portable.
#######################################################################################################

# Root folder of the project
ROOT_DIR = Path(__file__).resolve().parent

# Folder containing helper modules
UTILS_DIR = ROOT_DIR / "utils"

# Default embedding file loaded when the application starts
# The user can still choose another .npz file from the GUI
DEFAULT_NPZ_PATH = ROOT_DIR / "embeddings" / "well_embeddings_DINO_base.npz"

# CSV file used to map AHA wells to drug names
LABEL_CSV_PATH = UTILS_DIR / "labels.csv"

# Root folder containing the cell images displayed in the neighbor panel
# Expected structure: imgs/<dataset>/<plate>/<well>/cell_000.png
IMG_ROOT = ROOT_DIR / "imgs"

# Root folder of the original image dataset
# Expected structure: dataset/MyDB/<plate>/<well>.zip
DATASET_ROOT = ROOT_DIR / "dataset" / "MyDB"

# CSV file mapping plate/well IDs to drug names
UNIQUE_DRUGS_CSV_PATH = ROOT_DIR / "dataset" / "labels" / "unique_drugs.csv"


#######################################################################################################
# ANALYSIS SETTINGS
#######################################################################################################

TSNE_BACKEND = "sklearn"  # "sklearn", "cuml", or "sklearn"

# Distance used for t-SNE and nearest-neighbor search
# Accepted values: "cosine" or "euclidean"
DISTANCE = "cosine"

# Random seed used when subsampling points
RANDOM_SEED = 42

# Maximum number of wells displayed.
# Use None to load all wells.
MAX_POINTS = None