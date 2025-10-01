import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon


# 스크립트 실행과 모듈 실행 둘 다 지원
if __package__ is None:  # python src/app.py
    import os
    sys.path.append(os.path.dirname(__file__))
    from ui_main import MainWindow
else:  # python -m src.app
    from .ui_main import MainWindow

def main():
    # Qt6에서는 AA_UseHighDpiPixmaps 사용 금지/불필요 → 삭제
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/app.ico"))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
