from datetime import datetime
import pandas as pd
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal

class DataFrameModel(QAbstractTableModel):
    changed = pyqtSignal()  

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df
        self._upc_index = {}            # UPC(str) -> row(int)
        self._rebuild_upc_index()

    def _rebuild_upc_index(self):
        self._upc_index = {}
        upc_series = self._df["UPC"].astype(str)
        for i, v in enumerate(upc_series):
            self._upc_index[v.strip()] = i


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
                return value.strftime("%Y-%m-%d %H:%M:%S")
            return "" if pd.isna(value) else str(value)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._df.columns[section]
        else:
            return section + 1

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

    def set_dataframe(self, df: pd.DataFrame):
        self.beginResetModel()
        self._df = df
        self.endResetModel()
        self._rebuild_upc_index()

    def append_row(self, upc: str):
        now = pd.Timestamp(datetime.now())
        row = {"UPC": str(upc), "Qty": int(0), "LastScannedAt": now}
        self.beginInsertRows(QModelIndex(), len(self._df), len(self._df))
        self._df.loc[len(self._df)] = row
        self.endInsertRows()
        self._upc_index[str(upc).strip()] = len(self._df) - 1
        self.changed.emit()  # ✅ 변경 알림

    def dataframe(self) -> pd.DataFrame:
        return self._df

    def find_row_by_upc(self, upc: str) -> int:
        return self._upc_index.get(str(upc).strip(), -1)

    def add_qty(self, row_idx: int, amount: int):
        if row_idx < 0 or row_idx >= len(self._df):
            return
        self._df.at[row_idx, "Qty"] = int(self._df.at[row_idx, "Qty"] or 0) + int(amount)
        self._df.at[row_idx, "LastScannedAt"] = pd.Timestamp(datetime.now())
        top_left = self.index(row_idx, 0)
        bottom_right = self.index(row_idx, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
        self.changed.emit()  # ✅ 변경 알림

