from datetime import datetime
import re
import pandas as pd
from PyQt6.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, pyqtSignal
)

# ✅ UPC: 알파벳/숫자, 4자리 이상
_re_upc = re.compile(r"^[A-Za-z0-9]{4,}$")

class DataFrameModel(QAbstractTableModel):
    changed = pyqtSignal()      # 데이터 변경 신호
    error = pyqtSignal(str)     # 오류 발생 시 메세지 전달용

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df
        self._editable = False   # 더블클릭 편집 허용 여부

    def set_editable(self, on: bool):
        """편집 가능 모드 전환"""
        self._editable = bool(on)
        self.layoutChanged.emit()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._df)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            value = self._df.iat[index.row(), index.column()]
            if isinstance(value, pd.Timestamp):
                return "" if pd.isna(value) else value.strftime("%Y-%m-%d %H:%M:%S")
            return "" if (value is None or (isinstance(value, float) and pd.isna(value))) else str(value)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        return self._df.columns[section] if orientation == Qt.Orientation.Horizontal else section + 1

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        base = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        # ✅ 편집 모드일 때 UPC(0), Qty(1)만 수정 가능
        if self._editable and index.column() in (0, 1):
            return base | Qt.ItemFlag.ItemIsEditable
        return base

    def set_dataframe(self, df: pd.DataFrame):
        self.beginResetModel()
        self._df = df
        self.endResetModel()

    def dataframe(self) -> pd.DataFrame:
        return self._df

    def append_row(self, upc: str):
        now = pd.Timestamp(datetime.now())
        row = {"UPC": str(upc), "Qty": int(0), "LastScannedAt": now}
        self.beginInsertRows(QModelIndex(), len(self._df), len(self._df))
        self._df.loc[len(self._df)] = row
        self.endInsertRows()
        self.changed.emit()

    def find_row_by_upc(self, upc: str) -> int:
        matches = self._df.index[self._df["UPC"] == str(upc)].tolist()
        return matches[0] if matches else -1

    def add_qty(self, row_idx: int, amount: int):
        if 0 <= row_idx < len(self._df):
            self._df.at[row_idx, "Qty"] = int(self._df.at[row_idx, "Qty"] or 0) + int(amount)
            self._df.at[row_idx, "LastScannedAt"] = pd.Timestamp(datetime.now())
            top_left = self.index(row_idx, 0)
            bottom_right = self.index(row_idx, self.columnCount() - 1)
            self.dataChanged.emit(top_left, bottom_right,
                                  [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
            self.changed.emit()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """셀 편집 시 유효성 검사"""
        if role != Qt.ItemDataRole.EditRole or not index.isValid():
            return False
        r, c = index.row(), index.column()

        if c == 0:  # UPC
            new = str(value).strip().upper()
            if not _re_upc.match(new):
                self.error.emit("UPC는 알파벳/숫자만 가능하며 4자리 이상이어야 합니다.")
                return False
            # 중복 검사 (자기 자신 제외)
            dup = self._df.index[(self._df["UPC"] == new) & (self._df.index != r)]
            if len(dup) > 0:
                self.error.emit("중복된 UPC입니다.")
                return False
            self._df.at[r, "UPC"] = new

        elif c == 1:  # Qty
            s = str(value).strip()
            if not s.isdigit():
                self.error.emit("Qty는 정수만 입력할 수 있습니다.")
                return False
            self._df.at[r, "Qty"] = int(s)
            self._df.at[r, "LastScannedAt"] = pd.Timestamp(datetime.now())

        else:
            return False

        top_left = self.index(r, 0)
        bottom_right = self.index(r, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right,
                              [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
        self.changed.emit()
        return True

    # ✅ 팝업창 확인 시만 반영, LastScannedAt은 그대로 유지
    def update_row_values_without_touch(self, row: int, new_upc: str | None, new_qty: int | None) -> None:
        if row < 0 or row >= len(self._df):
            return

        cur_upc = str(self._df.at[row, "UPC"] or "").strip().upper()
        cur_qty = int(self._df.at[row, "Qty"] or 0)

        if new_upc is not None:
            upc = str(new_upc).strip().upper()
            if not _re_upc.match(upc):
                self.error.emit("UPC는 알파벳/숫자만 가능하며 4자리 이상이어야 합니다.")
                return
            dup = self._df.index[(self._df["UPC"] == upc) & (self._df.index != row)]
            if len(dup) > 0:
                self.error.emit("중복된 UPC입니다.")
                return
        else:
            upc = cur_upc

        if new_qty is not None:
            try:
                qty = int(new_qty)
            except Exception:
                self.error.emit("Qty는 정수만 입력할 수 있습니다.")
                return
        else:
            qty = cur_qty

        # LastScannedAt은 그대로 둠
        self._df.at[row, "UPC"] = upc
        self._df.at[row, "Qty"] = qty

        top_left = self.index(row, 0)
        bottom_right = self.index(row, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right,
                              [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
        self.changed.emit()
