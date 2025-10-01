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
    return len(t) >= min_len and t.isdigit()

def import_excel(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, dtype={"UPC": str}, engine="openpyxl")

    # 스키마 정렬
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[COLUMNS].copy()
    df["UPC"] = df["UPC"].astype("string")

    # ── 유효성 검사 ───────────────────────────────────────────
    errors = []

    # 1) 잘못된 UPC (비어있음/숫자 아님/길이<4)
    invalid_upc_mask = ~df["UPC"].apply(_is_valid_upc)
    if invalid_upc_mask.any():
        rows = (df.index[invalid_upc_mask] + 2).tolist()
        errors.append(f"잘못된 UPC 행: {rows}")

    # 2) 중복 UPC (그룹별 첫 번째만 표시)
    upc_norm = df["UPC"].astype(str).str.strip()
    dup_mask = upc_norm.duplicated(keep=False)

    if dup_mask.any():
        first_rows = []
        for _, group in df[dup_mask].groupby(upc_norm):
            first_idx = group.index.min()
            first_rows.append(int(first_idx) + 2)  # ← int()로 변환
        errors.append(f"중복된 UPC 행: {sorted(first_rows)}")

    # 3) 잘못된 Qty (정수만 허용, 빈칸/문자/소수 불가, 17.0은 허용)
    invalid_qty_mask = ~df["Qty"].apply(_is_valid_qty)
    if invalid_qty_mask.any():
        rows = (df.index[invalid_qty_mask] + 2).tolist()
        errors.append(f"잘못된 Qty 행: {rows}")

    if errors:
        # 위치만 알려달라는 요구에 맞춰 행 번호만 묶어 보고
        raise ValueError("\n".join(errors))
    # ──────────────────────────────────────────────────────────

    # 타입 정리
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
