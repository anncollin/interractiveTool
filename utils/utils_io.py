import pandas as pd
import numpy as np
import os 

#######################################################################################################
# NORM_TOKEN - Normalize a string by lowercasing and removing non-alphanumeric characters
# ----------------------------------------------------------------------------------------------------
#    Parameters:
#    ---------------------------
#    s : str
#        Input string to normalize.
#
#    Returns:
#    ---------------------------
#    s : str
#        Normalized version of the string.
#######################################################################################################
def norm_token(s: str) -> str:
    s = s.lower()
    return "".join(ch for ch in s if ch.isalnum())


#######################################################################################################
# ROBUST_READ_SQUARE_CSV - Read a square distance matrix from CSV
# ----------------------------------------------------------------------------------------------------
#    Parameters:
#    ---------------------------
#    path : str
#        Path to the CSV file containing a square matrix.
#
#    Returns:
#    ---------------------------
#    labels : list of str
#        Row/column labels extracted from the CSV (as strings).
#    M : np.ndarray
#        Square symmetric numeric matrix with zeros on diagonal.
#######################################################################################################
def robust_read_square_csv(path: str):
    try:
        df = pd.read_csv(path, index_col=0)
        if df.shape[0] != df.shape[1]:
            df = pd.read_csv(path, header=None)
    except Exception:
        df = pd.read_csv(path, header=None)

    if df.shape[0] != df.shape[1]:
        raise ValueError(f"Matrix must be square but got {df.shape}")

    labels = [str(x) for x in (df.index if not isinstance(df.index, pd.RangeIndex) else range(df.shape[0]))]
    M = df.apply(pd.to_numeric, errors="coerce").values.astype(float)

    # Fill NaNs with column means, then 0
    M = np.where(np.isfinite(M), M, np.nan)
    col_means = np.nanmean(M, axis=0)
    i, j = np.where(np.isnan(M))
    M[i, j] = col_means[j]
    M = np.nan_to_num(M, nan=0.0)

    # Symmetrize and zero diagonal
    M = 0.5 * (M + M.T)
    M[M < 0] = 0.0
    np.fill_diagonal(M, 0.0)
    return labels, M


#######################################################################################################
# MINMAX_OFFDIAGONAL - Min-max normalize off-diagonal entries to [0, 1]
# ----------------------------------------------------------------------------------------------------
#    Parameters:
#    ---------------------------
#    M : np.ndarray
#        Square matrix of distances.
#
#    Returns:
#    ---------------------------
#    Mnorm : np.ndarray
#        Normalized matrix with zeros on the diagonal.
#######################################################################################################
def minmax_offdiagonal(M: np.ndarray) -> np.ndarray:
    n = M.shape[0]
    mask = ~np.eye(n, dtype=bool)
    vals = M[mask]
    mn = float(np.nanmin(vals))
    mx = float(np.nanmax(vals))
    if mx > mn:
        M2 = (M - mn) / (mx - mn)
    else:
        M2 = M - mn
    np.fill_diagonal(M2, 0.0)
    return M2



#######################################################################################################
# get_zip_path_from_drug - Resolve absolute path to the ZIP file of a given drug
# ----------------------------------------------------------------------------------------------------
#    Parameters:
#    ---------------------------
#    drug_name : str
#        Drug name (case-insensitive) as it appears in the 3rd column of unique_drugs.csv.
#
#    Returns:
#    ---------------------------
#    zip_path : str
#        Absolute path to the corresponding ZIP file in dataset/MyDB/<plate>/<well>.zip
#######################################################################################################
def get_zip_path_from_drug(drug_name):
    # Absolute path to unique_drugs.csv
    csv_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "labels", "unique_drugs.csv")
    )

    # Load the CSV and search for the drug
    df = pd.read_csv(csv_path, header=None)
    match = df[df.iloc[:, 2].astype(str).str.strip().str.lower() == drug_name.strip().lower()]

    if match.empty:
        raise FileNotFoundError(f"Drug {drug_name!r} not found in {csv_path}")

    plate = str(match.iloc[0, 0]).strip()
    well = str(match.iloc[0, 1]).strip()

    # --- Fix: pad well ID to 6 digits ---
    well_padded = well.zfill(6)

    # Build absolute path to the ZIP file under dataset/MyDB/
    base_dataset_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "MyDB")
    )
    zip_path = os.path.join(base_dataset_path, plate, f"{well_padded}.zip")

    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")

    return zip_path
