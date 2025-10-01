# UPC Counter Application

A desktop application built with **Python (PyQt6, pandas, openpyxl)** for scanning and managing UPC codes with Excel import/export support.

---

## 📖 [한글 매뉴얼](#korean-manual)

---

## 📥 Download

👉 [Download UPC Counter App (EXE)](https://drive.google.com/file/d/1Y7H2GlVVlCKQJ67g01azLE-zK5nimbG_/view?usp=drive_link)

---

## 📖 English Manual

### Features
- **Excel Import / Open**: Load UPC and quantity data from `.xlsx` files.
- **Save / Save As**: Save your current UPC table back to Excel.
- **UPC Handling**:  
  - Enter ≥ 4 alphanumeric characters (digits or letters) → registered as new UPC (or select existing UPC if already registered).  
  - Enter numbers **1–10** → adds quantity to the currently selected UPC row.
- **Validation & Errors**:  
  - ✅ Allowed: UPC with **numbers and/or alphabets** (minimum 4 characters).  
  - ❌ Error cases:  
    - UPC cell is empty.  
    - Qty cell is empty or not a number.  
    - Duplicate UPC detected in Excel import (first occurrence kept, duplicates cause error message).  
    - Input shorter than 4 characters (and not 1–10).  
    - Input contains spaces or special characters (only digits and alphabets allowed).  
- **Last Scanned At**: Each change updates the timestamp automatically.  
- **Buffer Input**: Keyboard input is collected in the buffer field at the bottom and processed on `Enter`.

### Shortcuts
- **Ctrl+O** → Open Excel  
- **Ctrl+S** → Save  
- **Ctrl+Shift+S** → Save As  
- **Esc** → Clear Buffer  

### How to Use
1. Launch `upc-counter.exe` (download above).  
2. Use the **buffer input field** at the bottom to scan UPC codes or type manually.  
3. Press **Enter** after input.  
   - ≥ 4 alphanumeric characters: UPC registration.  
   - 1–10: Quantity increment for current row.  
4. Save results back to Excel with **Save** or **Save As**.  

---

## 📖 한글 매뉴얼 {#korean-manual}

### 주요 기능
- **엑셀 불러오기(Open)**: `.xlsx` 파일에서 UPC/수량 데이터를 불러옵니다.  
- **저장(Save / Save As)**: 현재 테이블을 엑셀 파일로 저장합니다.  
- **UPC 처리 규칙**:  
  - **숫자와 알파벳**을 포함한 **4글자 이상** 입력 → 새로운 UPC로 등록 (이미 있으면 해당 행 선택).  
  - 숫자 **1~10** 입력 → 현재 선택된 행의 수량(Qty)을 추가.  
- **검증 및 오류 발생 조건**:  
  - ✅ 허용: 숫자, 알파벳 조합(4글자 이상).  
  - ❌ 오류 발생:  
    - UPC가 비어 있을 때.  
    - Qty가 비어 있거나 숫자가 아닐 때.  
    - 엑셀 불러오기 시 중복된 UPC가 존재할 때 (첫 번째만 인정, 나머지는 오류 메시지).  
    - 입력이 4글자 미만(단, 1~10 수량 입력은 예외).  
    - 공백이나 특수문자가 포함된 경우.  
- **최근 스캔 시간**: 변경 시 `LastScannedAt` 자동 갱신.  
- **버퍼 입력 필드**: 하단 입력창에 코드가 모이고 `Enter` 입력 시 처리됩니다.  

### 단축키
- **Ctrl+O** → 엑셀 불러오기  
- **Ctrl+S** → 저장  
- **Ctrl+Shift+S** → 다른 이름으로 저장  
- **Esc** → 입력 버퍼 초기화  

### 사용 방법
1. 위의 **[다운로드 링크](https://drive.google.com/file/d/1Y7H2GlVVlCKQJ67g01azLE-zK5nimbG_/view?usp=drive_link)**에서 `upc-counter.exe`를 다운로드합니다.  
2. 프로그램 실행 후, 하단 입력창에 UPC 코드 또는 수량을 입력합니다.  
3. **Enter**를 누르면:  
   - 4글자 이상 (숫자/알파벳 조합) → UPC 등록.  
   - 1~10 → 선택된 행의 수량 증가.  
4. **저장(Save / Save As)** 기능을 통해 엑셀 파일로 결과를 저장합니다.  
