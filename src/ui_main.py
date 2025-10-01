from PyQt6.QtWidgets import (
    QMainWindow, QTableView, QStatusBar, QLineEdit,
    QWidget, QVBoxLayout, QToolBar, QFileDialog, QMessageBox, QSizePolicy
)
from PyQt6.QtGui import QKeySequence, QAction, QIcon 
from PyQt6.QtCore import Qt

import os
import pandas as pd

from model.store import make_empty_df
from model.dataframe_model import DataFrameModel


class MainWindow(QMainWindow):
    UPC_MIN_LEN = 4

    def __init__(self):
        super().__init__()
        self.setWindowTitle("UPC Counter")
        self.resize(900, 600)

        self.setWindowIcon(QIcon("../assets/app.ico"))

        # 상태들
        self.model = DataFrameModel(make_empty_df())
        self.current_row = -1
        self.buffer = []
        self.current_file: str | None = None   # ✅ 현재 열려있는 파일 경로
        self.is_dirty: bool = False            # ✅ 수정 여부(*)

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

        # 상태바 + 입력 버퍼 표시 필드(가로/세로 크게, 포커스 가시화)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.buffer_display = QLineEdit()
        self.buffer_display.setReadOnly(True)
        self.buffer_display.setPlaceholderText("입력 버퍼 — Enter로 확정")
        self.buffer_display.setMinimumHeight(40)
        self.buffer_display.setMinimumWidth(600)
        self.buffer_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.status_bar.addPermanentWidget(self.buffer_display)
        # Enter를 여기서 눌러도 처리되도록
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

        # 중앙 레이아웃
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.table)
        self.setCentralWidget(central)

        self._init_actions()
        self._connect_signals()
        self._update_title()

    # ─────────────────────────────────────────────────────────────
    # UI/액션
    # ─────────────────────────────────────────────────────────────
    def _init_actions(self):
        tb = QToolBar("Main")
        self.addToolBar(tb)

        # Import
        act_import = QAction("Open Excel", self)
        act_import.setShortcut(QKeySequence("Ctrl+I"))
        act_import.triggered.connect(self.on_import_excel)
        tb.addAction(act_import)

        # Save (현재 파일에 저장)
        act_save = QAction("Save", self)
        act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self.on_save)
        tb.addAction(act_save)

        # Save As (항상 경로 묻기)
        act_save_as = QAction("Save As...", self)
        act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_save_as.triggered.connect(self.on_save_as)
        tb.addAction(act_save_as)

        # Export Excel… 을 Save As와 동일하게 쓰고 싶으면 아래 주석 해제
        # act_export = QAction("Export Excel...", self)
        # act_export.setShortcut(QKeySequence("Ctrl+E"))
        # act_export.triggered.connect(self.on_save_as)
        # tb.addAction(act_export)

        act_clear = QAction("Clear Buffer", self)
        act_clear.setShortcut(QKeySequence("Esc"))
        act_clear.triggered.connect(self.clear_buffer)
        tb.addAction(act_clear)

    def _connect_signals(self):
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)

    # ─────────────────────────────────────────────────────────────
    # 상태 업데이트
    # ─────────────────────────────────────────────────────────────
    def _update_title(self):
        name = (os.path.basename(self.current_file) if self.current_file else "Untitled")
        star = "*" if self.is_dirty else ""
        self.setWindowTitle(f"UPC Counter - {name}{star}")

    def mark_dirty(self):
        if not self.is_dirty:
            self.is_dirty = True
            self._update_title()

    # ─────────────────────────────────────────────────────────────
    # 선택 변경
    # ─────────────────────────────────────────────────────────────
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

    # ─────────────────────────────────────────────────────────────
    # Import / Save / Save As
    # ─────────────────────────────────────────────────────────────
    def on_import_excel(self):
        from model.io_excel import import_excel
        path, _ = QFileDialog.getOpenFileName(self, "Import Excel", "", "Excel Files (*.xlsx)")
        if not path:
            return
        try:
            df = import_excel(path)
            self.model.set_dataframe(df)
            self.current_file = path     # ✅ 현재 파일 기억
            self.is_dirty = False        # ✅ 로드 직후는 clean
            self._update_title()
            self.status_bar.showMessage(f"가져오기 완료: {os.path.basename(path)}", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Import 실패", str(e))

    def on_save(self):
        """현재 파일로 저장. 경로가 없으면 Save As로 위임."""
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
            self.current_file = path     # ✅ 새 경로 기억
            self.is_dirty = False
            self._update_title()
            self.status_bar.showMessage(f"저장 완료: {os.path.basename(path)}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Save As 실패", str(e))

    # ─────────────────────────────────────────────────────────────
    # 입력 버퍼/키 처리
    # ─────────────────────────────────────────────────────────────
    def keyPressEvent(self, event):
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
            # 입력 처리 (UPC 추가/선택, Qty 증가 등)
            handle_input(self, raw)
            # ✅ 데이터 변경 가능성이 있으므로 dirty 마킹
            self.mark_dirty()

    def select_row(self, row_idx: int):
        if row_idx < 0:
            return
        self.table.clearSelection()
        self.table.selectRow(row_idx)
        self.current_row = row_idx

    # (선택) 창 닫을 때 저장 여부 확인을 원하면 아래 주석 해제
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
