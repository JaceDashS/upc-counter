from PyQt6.QtWidgets import (
    QMainWindow, QTableView, QStatusBar, QLineEdit,
    QWidget, QVBoxLayout, QToolBar, QFileDialog, QMessageBox,
    QSizePolicy, QAbstractItemView, QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtGui import QKeySequence, QAction, QIcon
from PyQt6.QtCore import Qt, QEvent

import os

from model.store import make_empty_df
from model.dataframe_model import DataFrameModel


class EditRowDialog(QDialog):
    """더블클릭 후 뜨는 팝업: 여기서 값 수정 → 확인 시에만 반영"""
    def __init__(self, parent, upc: str, qty: int):
        super().__init__(parent)
        self.setWindowTitle("행 수정")
        self.setModal(True)

        self.upc_edit = QLineEdit(self)
        self.upc_edit.setText(str(upc))

        self.qty_edit = QLineEdit(self)
        self.qty_edit.setText(str(qty))

        form = QFormLayout(self)
        form.addRow("UPC (영문/숫자, 4+):", self.upc_edit)
        form.addRow("Qty (정수):", self.qty_edit)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self
        )
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

        self._result = None  # (upc, qty)

    def _on_accept(self):
        upc = (self.upc_edit.text() or "").strip().upper()
        qty_s = (self.qty_edit.text() or "").strip()
        # 1차 간단 검증(정확 검증은 모델에서 최종 수행)
        if len(upc) < 4 or (not upc.isalnum()):
            QMessageBox.warning(self, "입력 오류", "UPC는 영문/숫자만 가능하며 4자 이상이어야 합니다.")
            return
        if not qty_s.isdigit():
            QMessageBox.warning(self, "입력 오류", "Qty는 정수만 입력할 수 있습니다.")
            return
        self._result = (upc, int(qty_s))
        self.accept()

    def result_values(self):
        return self._result  # (upc, qty) or None


class MainWindow(QMainWindow):
    UPC_MIN_LEN = 4

    def __init__(self):
        super().__init__()
        self.setWindowTitle("UPC Counter")
        self.resize(900, 600)

        # 앱 아이콘
        self.setWindowIcon(QIcon("../assets/app.ico"))

        # 상태
        self.model = DataFrameModel(make_empty_df())
        self.current_row = -1
        self.buffer = []
        self.current_file: str | None = None
        self.is_dirty: bool = False
        self.edit_warning_shown: bool = False  # 더블클릭 수정 경고 1회용

        # 테이블
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setColumnWidth(0, 260)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 200)
        # 모든 셀 직접 편집 비활성 (수정은 팝업으로만)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # 더블클릭 감지 (viewport로 설치 권장)
        self.table.viewport().installEventFilter(self)

        # 모델 시그널
        self.model.changed.connect(self.mark_dirty)
        self.model.error.connect(lambda msg: QMessageBox.warning(self, "수정 오류", msg))

        # 상태바 + 입력 버퍼
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.buffer_display = QLineEdit()
        self.buffer_display.setReadOnly(True)
        self.buffer_display.setPlaceholderText("입력 버퍼 — Enter로 확정")
        self.buffer_display.setMinimumHeight(40)
        self.buffer_display.setMinimumWidth(600)
        self.buffer_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.buffer_display.returnPressed.connect(self.process_buffer)
        self.buffer_display.setStyleSheet("""
            QLineEdit {
                font-size: 14pt;
                padding: 8px;
                border: 2px solid gray;
                border-radius: 4px;
                background-color: #f9f9f9;
                color: black;
                selection-background-color: #0078d7;
                selection-color: white;
            }
            QLineEdit::placeholder {
                font-size: 12pt;
                color: gray;
            }
            QLineEdit:focus {
                border: 2px solid #0078d7;
                background-color: #ffffff;
                color: black;
            }
            QLineEdit:!focus {
                border: 2px solid #d9534f;
                background-color: #fff3f3;
                color: black;
            }
        """)
        self.status_bar.addPermanentWidget(self.buffer_display)

        # 중앙 레이아웃
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.table)
        self.setCentralWidget(central)

        # 액션/단축키
        self._init_actions()
        self._connect_signals()
        self._update_title()

    # 액션/단축키
    def _init_actions(self):
        tb = QToolBar("Main")
        self.addToolBar(tb)

        act_open = QAction("Open Excel", self)
        act_open.setShortcut(QKeySequence("Ctrl+O"))
        act_open.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        act_open.triggered.connect(self.on_open_excel)
        tb.addAction(act_open)
        self.addAction(act_open)

        act_save = QAction("Save", self)
        act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        act_save.triggered.connect(self.on_save)
        tb.addAction(act_save)
        self.addAction(act_save)

        act_save_as = QAction("Save As...", self)
        act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_save_as.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        act_save_as.triggered.connect(self.on_save_as)
        tb.addAction(act_save_as)
        self.addAction(act_save_as)

        act_clear = QAction("Clear Buffer", self)
        act_clear.setShortcut(QKeySequence("Esc"))
        act_clear.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        act_clear.triggered.connect(self.clear_buffer)
        tb.addAction(act_clear)
        self.addAction(act_clear)

    def _connect_signals(self):
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)

    # 제목/더티 표시
    def _update_title(self):
        name = (os.path.basename(self.current_file) if self.current_file else "Untitled")
        star = "*" if self.is_dirty else ""
        self.setWindowTitle(f"UPC Counter - {name}{star}")

    def mark_dirty(self):
        if not self.is_dirty:
            self.is_dirty = True
            self._update_title()

    # 선택 변경
    def on_selection_changed(self, *_):
        indexes = self.table.selectionModel().selectedRows()
        if indexes:
            self.current_row = indexes[0].row()
            upc = self.model.dataframe().iat[self.current_row, 0]
            qty = self.model.dataframe().iat[self.current_row, 1]
            self.status_bar.showMessage(f"선택됨: UPC={upc}, Qty={qty}", 3000)
        else:
            self.current_row = -1
            self.status_bar.showMessage("선택된 행이 없습니다.", 1500)

    # Open / Save / Save As
    def on_open_excel(self):
        from model.io_excel import import_excel
        path, _ = QFileDialog.getOpenFileName(self, "Open Excel", "", "Excel Files (*.xlsx)")
        if not path:
            return
        try:
            df = import_excel(path)
            self.model.set_dataframe(df)
            self.current_file = path
            self.is_dirty = False
            self._update_title()
            self.status_bar.showMessage(f"불러오기 완료: {os.path.basename(path)}", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Open 실패", str(e))

    def on_save(self):
        from model.io_excel import export_excel
        if self.current_file:
            try:
                export_excel(self.model.dataframe(), self.current_file)
                self.is_dirty = False
                self._update_title()
                self.status_bar.showMessage(f"저장 완료: {os.path.basename(self.current_file)}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Save 실패", str(e))
        else:
            self.on_save_as()

    def on_save_as(self):
        from model.io_excel import export_excel
        path, _ = QFileDialog.getSaveFileName(self, "Save As", "upc_data.xlsx", "Excel Files (*.xlsx)")
        if not path:
            return
        try:
            export_excel(self.model.dataframe(), path)
            self.current_file = path
            self.is_dirty = False
            self._update_title()
            self.status_bar.showMessage(f"저장 완료: {os.path.basename(path)}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Save As 실패", str(e))

    # 키 처리 / 입력 버퍼
    def keyPressEvent(self, event):
        if event.modifiers() & (
            Qt.KeyboardModifier.ControlModifier
            | Qt.KeyboardModifier.AltModifier
            | Qt.KeyboardModifier.MetaModifier
        ):
            return super().keyPressEvent(event)

        key = event.key()
        text = event.text()

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.process_buffer()
            return

        if key == Qt.Key.Key_Escape:
            self.clear_buffer()
            return

        if text and not text.isspace():
            self.buffer.append(text)
            self.update_buffer_display()
        else:
            super().keyPressEvent(event)

    def update_buffer_display(self):
        self.buffer_display.setText("".join(self.buffer))

    def clear_buffer(self):
        self.buffer = []
        self.update_buffer_display()
        self.status_bar.showMessage("버퍼를 지웠습니다.", 1500)

    def process_buffer(self):
        from controller.input_handler import handle_input
        raw = "".join(self.buffer).strip()
        self.clear_buffer()
        if raw:
            handle_input(self, raw)
            self.mark_dirty()

    def select_row(self, row_idx: int):
        if row_idx < 0:
            return
        self.table.clearSelection()
        self.table.selectRow(row_idx)
        self.current_row = row_idx

    # 더블클릭 → (1회 경고) → 팝업에서 수정 → 확인 시만 반영(LastScannedAt 유지)
    def eventFilter(self, obj, event):
        if obj is self.table.viewport() and event.type() == QEvent.Type.MouseButtonDblClick:
            idx = self.table.indexAt(event.position().toPoint())
            if not idx.isValid():
                return True

            if not self.edit_warning_shown:
                reply = QMessageBox.warning(
                    self,
                    "편집 모드",
                    "더블클릭으로 행을 팝업에서 수정할 수 있습니다.\n"
                    "- UPC: 알파벳/숫자, 4자 이상, 중복 불가\n"
                    "- Qty: 정수만\n\n"
                    "계속하시겠습니까?",
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
                )
                if reply != QMessageBox.StandardButton.Ok:
                    return True
                self.edit_warning_shown = True

            r = idx.row()
            cur_upc = str(self.model.dataframe().iat[r, 0] or "")
            cur_qty = int(self.model.dataframe().iat[r, 1] or 0)

            dlg = EditRowDialog(self, cur_upc, cur_qty)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                upc, qty = dlg.result_values()
                self.model.update_row_values_without_touch(r, upc, qty)  # ⬅️ 타임스탬프 유지
                self.mark_dirty()
            return True
        return super().eventFilter(obj, event)

    # (선택) 창 닫을 때 저장 여부 묻기
    def closeEvent(self, event):
        if self.is_dirty:
            reply = QMessageBox.question(
                self, "저장", "변경사항을 저장하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.on_save()
                event.accept()
            elif reply == QMessageBox.StandardButton.No:
                event.accept()
            else:
                event.ignore()
