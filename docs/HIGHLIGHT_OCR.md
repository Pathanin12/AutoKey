# Highlight OCR — อ่านข้อความไทยจาก Selection บนหน้าจอ

โมดูลนี้อ่านข้อความที่ผู้ใช้ **Highlight/เลือก** บน Desktop app ที่ **Copy ไม่ได้** โดยใช้:

```
Screenshot → Detect Highlight → Bounding Box → Crop บรรทัด → Preprocess → OCR → Text
```

ไม่ใช้ Clipboard, Google Cloud หรือ API เสียเงิน — รัน **local** ทั้งหมด

---

## ติดตั้ง

### 1) Python 3.12+ และ dependencies พื้นฐาน

```bash
cd AutoKey
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Tesseract + ภาษาไทย (ขั้นต่ำ)

**Windows**
```powershell
choco install tesseract -y
# ดาวน์โหลด tha.traineddata ไปที่ tessdata
```

**macOS (dev/test)**
```bash
brew install tesseract tesseract-lang
```

### 3) OCR engines เพิ่มเติม (แนะนำเพื่อความแม่นภาษาไทย)

```bash
pip install easyocr

# PaddleOCR (แม่นสุดบ่อยครั้ง แต่ใหญ่) — Windows CPU
pip install paddlepaddle==2.6.2 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
pip install paddleocr>=2.7.0
```

หรือติดตั้งครบจากไฟล์:
```bash
pip install -r requirements-highlight-ocr.txt
```

---

## รัน Demo

1. เปิดโปรแกรมที่ต้องการ (เช่น Express Accounting)
2. **Highlight** ข้อความที่ต้องการอ่าน
3. รัน:

```bash
python tools/highlight_ocr_demo.py --delay 3 --engine auto --debug
```

### พารามิเตอร์สำคัญ

| พารามิเตอร์ | ค่า default | ความหมาย |
|-------------|-------------|----------|
| `--delay` | 3 | วินาทีรอก่อนจับภาพ |
| `--engine` | auto | `auto` / `tesseract` / `easyocr` / `paddleocr` |
| `--debug` | off | บันทึกภาพ debug |
| `--min-color-distance` | 12 | threshold ความต่างสีจากพื้นหลัง (LAB) |
| `--highlight-percentile` | 97.5 | percentile ของ pixel ที่ถือว่า highlight |
| `--line-expand-y` | 6 | ขยาย bbox แนวตั้ง (px) |
| `--upscale` | 3.0 | ขยายภาพก่อน OCR |

ผลลัพธ์ JSON:
```bash
python tools/highlight_ocr_demo.py --delay 2 --json
```

---

## โครงสร้างโค้ด

| ฟังก์ชัน | ไฟล์ |
|---------|------|
| `capture_screen()` | `services/highlight_ocr/screen_capture_service.py` |
| `detect_highlight()` | `services/highlight_ocr/highlight_detect_service.py` |
| `get_highlight_bbox()` | `services/highlight_ocr/highlight_detect_service.py` |
| `crop_highlight_region()` | `services/highlight_ocr/crop_service.py` |
| `preprocess_image()` | `services/highlight_ocr/preprocess_service.py` |
| `run_ocr()` | `services/highlight_ocr/ocr_engine_service.py` |
| `filter_ocr_by_bbox()` | `services/highlight_ocr/filter_service.py` |
| `get_selected_text()` | `services/highlight_ocr/highlight_ocr_service.py` |

Models: `models/highlight_bbox.py`, `models/highlight_ocr_settings.py`, `models/highlight_ocr_result.py`, `models/ocr_word_result.py`

---

## วิธีปรับ Threshold Highlight

Highlight **ไม่ hard-code สีเดียว** — ใช้ความต่างจาก **สีพื้นหลังรอบขอบจอ** ใน LAB + กรณีเทา (HSV)

### ถ้า detect ไม่เจอ highlight
- **ลด** `--min-color-distance` (เช่น 12 → 8)
- **ลด** `--highlight-percentile` (เช่น 97.5 → 95)
- เปิด `--debug` ดู `highlight_detected.png`

### ถ้า detect กินพื้นที่เกิน / จับบรรทัดข้างเคียง
- **เพิ่ม** `--min-color-distance`
- **เพิ่ม** `--highlight-percentile`
- **ลด** `--line-expand-y`

### สี highlight ที่รองรับ
- น้ำเงิน / ฟ้า (selection ทั่วไป)
- เทา (low saturation + ต่างจากพื้นหลัง)
- สีอื่นที่ **ต่างจากพื้นหลัง** มากพอใน LAB space

ปรับถาวรในโค้ด: `HighlightOcrSettings` ใน `models/highlight_ocr_settings.py`

---

## วิธีปรับ OCR ภาษาไทย

### เปรียบเทียบ Engine (เรียงตามความแม่นไทยที่มักได้)

1. **PaddleOCR** — มักดีสุดบน screenshot UI ไทย (ติดตั้งหนัก)
2. **EasyOCR** — ดีรองลงมา ติดตั้งง่ายกว่า
3. **Tesseract** — มีใน AutoKey อยู่แล้ว; ต้อง **preprocess ดี** + ใช้ `tha`

ใช้ `--engine auto` ให้ระบบลองทุก engine ที่ติดตั้งแล้วเลือก confidence สูงสุด

### Preprocess ที่ใช้อยู่
- Grayscale → contrast → denoise
- Upscale 3x (ปรับ `--upscale` 2–4)
- ลองทั้ง raw, adaptive threshold, Otsu

### Tesseract tips
- ใช้ lang `tha`
- PSM 7 / 6 / 13 (ตั้งใน settings)
- ขยายภาพก่อน OCR สำคัญมาก

---

## Debug Images

เมื่อเปิด `--debug` จะได้ใน `debug/highlight_ocr/`:

| ไฟล์ | ความหมาย |
|------|----------|
| `original.png` | ภาพหน้าจอเต็ม |
| `highlight_detected.png` | กรอบแดง = highlight, เขียว = OCR line, ฟ้า = คำ |
| `cropped.png` | crop ตาม highlight |
| `preprocessed.png` | ภาพหลัง preprocess |
| `ocr_result.png` | สรุปผล |

---

## DPI Scaling (100% / 125% / 150%)

- ใช้ **logical pixels** จาก `pyautogui.screenshot()` — ไม่ hard-code พิกัด
- อ่าน **DPI scale** อัตโนมัติบน Windows (`GetDeviceCaps`)
- threshold ขยาย/หดตามขนาด bbox ไม่ใช่พิกัดคงที่

---

## ใช้ใน AutoKey / Automation

```python
from models.highlight_ocr_settings import HighlightOcrSettings
from services.highlight_ocr import get_selected_text

settings = HighlightOcrSettings(primary_engine="auto", debug=False)
result = get_selected_text(settings)
print(result.text)           # ข้อความรวม (หลายบรรทัด = คั่นด้วย newline)
print(result.average_confidence)
for line in result.lines:
    print(line.text, line.confidence, line.bbox.as_tuple())
```

---

## ข้อจำกัด

- ต้องมี highlight ที่มองเห็นชัดบนหน้าจอ
- PaddleOCR / EasyOCR ครั้งแรกโหลด model ช้า
- ทดสอบจริงแนะนำบน **Windows** (เป้าหมาย Express Accounting)
