import math
import pandas as pd
from .store import COLUMNS

def _is_valid_qty(x) -> bool:
    if pd.isna(x): return False
    if isinstance(x, int): return True
    if isinstance(x, float): return math.isfinite(x) and float(x).is_integer()
    s = str(x).strip()
    return s.isdigit()

def _is_valid_upc(s: object, min_len: int = 4) -> bool:
    if pd.isna(s): return False
    t = str(s).strip()
    # ✅ 알파벳/숫자만 허용 + 길이 검사
    return len(t) >= min_len and t.isalnum()

def import_excel(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, dtype={"UPC": str}, engine="openpyxl")

    # 스키마 정렬
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[COLUMNS].copy()

    # ✅ 문자열/트림/대문자 정규화 (대소문자 섞여 있어도 동일 취급)
    df["UPC"] = df["UPC"].astype("string").str.strip().str.upper()

    # 1) 잘못된 UPC (빈값/비알파넘/길이<4)
    invalid_upc_mask = ~df["UPC"].apply(_is_valid_upc)
    if invalid_upc_mask.any():
        rows = (df.index[invalid_upc_mask] + 2).tolist()
        raise ValueError(f"잘못된 UPC 행: {rows}")

    # 2) 중복 UPC (그룹별 첫 번째만 표시) — 대문자 기준
    upc_norm = df["UPC"]  # 이미 대문자/트림됨
    dup_mask = upc_norm.duplicated(keep=False)
    if dup_mask.any():
        first_rows = []
        for _, group in df[dup_mask].groupby(upc_norm):
            first_idx = group.index.min()
            first_rows.append(int(first_idx) + 2)
        first_rows.sort()
        raise ValueError(f"중복된 UPC 행: {first_rows}")

    # 3) Qty 유효성 (그대로)
    invalid_qty_mask = ~df["Qty"].apply(_is_valid_qty)
    if invalid_qty_mask.any():
        rows = (df.index[invalid_qty_mask] + 2).tolist()
        raise ValueError(f"잘못된 Qty 행: {rows}")

    # 타입 정리 (그대로)
    def _to_int(x):
        if isinstance(x, float): return int(x)
        return int(str(x).strip())

    df["Qty"] = df["Qty"].apply(_to_int).astype("int64")
    df["LastScannedAt"] = pd.to_datetime(df["LastScannedAt"], errors="coerce")
    return df

def export_excel(df: pd.DataFrame, path: str):
    df = df.copy()
    df["UPC"] = df["UPC"].astype("string")
    df.to_excel(path, index=False, engine="openpyxl")
