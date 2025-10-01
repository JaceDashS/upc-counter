import re
from PyQt6.QtWidgets import QMessageBox

QTY_PATTERN = re.compile(r"^(?:10|[1-9])$")
UPC_ALLOWED_PATTERN = re.compile(r"^[A-Za-z0-9]+$")  # 영문 + 숫자만 허용

def handle_input(window, raw: str):
    token = (raw or "").strip()
    if not token:
        return

    # 4글자 이상이면 UPC 후보
    if len(token) >= window.UPC_MIN_LEN:
        # 영문/숫자 외 문자가 있으면 실패
        if not UPC_ALLOWED_PATTERN.match(token):
            QMessageBox.warning(window, "입력 오류", "UPC는 영어와 숫자만 입력 가능합니다.")
            return
        handle_upc(window, token)
        return

    # 1~10 숫자는 수량
    if QTY_PATTERN.match(token):
        if window.current_row < 0:
            QMessageBox.warning(window, "선택 필요", "수량을 더하려면 먼저 행을 선택하거나 UPC를 스캔하세요.")
            return
        amount = int(token)
        window.model.add_qty(window.current_row, amount)
        window.status_bar.showMessage(f"Qty +{amount}", 2000)
        return

    # 그 외는 오류
    QMessageBox.warning(window, "입력 오류", "유효하지 않은 입력입니다. (UPC ≥ 4글자 또는 1~10 숫자)")

def handle_upc(window, upc: str):
    row = window.model.find_row_by_upc(upc)
    if row >= 0:
        # 팝업 없이 조용히 선택만
        window.select_row(row)
        # 상태바 알림이 필요 없으면 아래 줄을 제거하세요.
        window.status_bar.showMessage(f"UPC 선택됨: {upc}", 2000)
    else:
        window.model.append_row(upc)
        window.select_row(len(window.model.dataframe()) - 1)
        window.status_bar.showMessage(f"신규 UPC 추가: {upc}", 3000)
