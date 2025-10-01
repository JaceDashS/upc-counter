import pandas as pd

COLUMNS = ["UPC", "Qty", "LastScannedAt"]

def make_empty_df() -> pd.DataFrame:
    df = pd.DataFrame(columns=COLUMNS)
    df["UPC"] = df["UPC"].astype("string")
    df["Qty"] = pd.Series(dtype="int64")
    df["LastScannedAt"] = pd.Series(dtype="datetime64[ns]")
    return df
