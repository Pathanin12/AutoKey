# AutoKey

โปรแกรม Auto สำหรับ Express Accounting บน Windows โดยอ่านข้อมูลจาก Excel และกรอก **สมุดรายวันจ่าย (PV)** อัตโนมัติ

**เวอร์ชัน:** `1.0.0` (ดู `constants/version.py`)

## ความต้องการ

- Windows 10/11
- Express Accounting — เปิดอยู่หน้า **Dialog เลือกข้อมูล** ก่อนกดเริ่ม
- จอ 1920×1080, scale 100%
- Python 3.11+ (สำหรับพัฒนา) / ดาวน์โหลด `.exe` จาก GitHub Actions (Windows)

## ดาวน์โหลด Windows (.exe)

1. ไปที่ **Actions** → workflow **Build Windows** → เลือก run ล่าสุด
2. ดาวน์โหลด artifact `AutoKey-windows-…` → ได้ `AutoKey.exe`
3. วาง `config.yaml` และโฟลเดอร์ `assets/` ไว้ข้าง exe (PyInstaller รวมให้แล้ว)

Release อย่างเป็นทางการ: push tag `v1.0.0` → GitHub สร้าง Release พร้อมแนบ exe

## Build Windows (local / CI)

```bash
pip install -r requirements.txt -r requirements-build.txt
pyinstaller --noconfirm AutoKey.spec
# ได้ dist/AutoKey.exe — icon + version ฝังใน exe แล้ว
```

GitHub Actions: `.github/workflows/build-windows.yml` (build อัตโนมัติเมื่อ push `main`)

## ติดตั้ง

### Mac (Apple Silicon M1/M2/M3/M4) — ดู UI / ทดสอบ Excel

```bash
brew install python@3.13 python-tk@3.13
cd AutoKey
./run.sh
```

ใช้ **Python 3.13 จาก Homebrew** — ไม่ใช้ Python 3.9 เก่าของ macOS

### Windows — รัน Auto จริง

```bash
cd AutoKey
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## ใช้งาน

1. เปิด Express Accounting และ Login ให้เรียบร้อย
2. รันโปรแกรม

```bash
python main.py
```

3. เลือกไฟล์ Excel — โปรแกรมอ่านชีตและจำนวนรายการอัตโนมัติ
4. กรอก **รายละเอียด** (ใช้เหมือนกันทุกแถวในรอบนั้น)
5. ตั้งวันที่ PV หรือเลือกใช้วันที่ทำการจาก Express
6. กด **เริ่ม**

## จับภาพ Template (ครั้งแรกบนเครื่อง Windows)

```bash
python tools/capture_templates.py
```

บันทึกภาพไปที่ `assets/templates/`:

| ไฟล์ | ใช้สำหรับ |
|------|-----------|
| `pv_new.png` | ปุ่ม New ใน PV |
| `pv_save.png` | ปุ่ม Save |
| `btn_ok.png` | ปุ่ม ตกลง |
| `wt_dialog.png` | Dialog ภาษีหัก ณ ที่จ่าย |
| `tax_invoice_dialog.png` | Dialog ใบกำกับภาษีซื้อ |

## โครงสร้าง

```
AutoKey/
├── main.py
├── config.yaml
├── constants/routes.py
├── models/
├── services/
├── topics/ka_tam/
├── ui/
├── assets/icon/          # app_icon.png + app_icon.ico
├── packaging/            # version_info.txt สำหรับ Windows exe
├── AutoKey.spec          # PyInstaller
├── .github/workflows/    # build-windows.yml
```

## Flow สมุดรายวันจ่าย

1. ไปเมนู `5 > 1 > 2` (บัญชี > ลงประจำวัน > สมุดรายวันจ่าย)
2. สร้างรายการใหม่
3. กรอกรายละเอียด
4. บัญชี `5330-05` เดบิต = ยอดบริการ
5. บัญชี `1154-00` เดบิต = ภาษีซื้อ + กรอกใบกำกับภาษีซื้อ
6. บัญชี `1111-00` เครดิต = ยอดรวม - WT
7. กรอกภาษีหัก ณ ที่จ่าย
8. Save แล้ววนทำแถวถัดไป

## หมายเหตุ

- ย้ายเมาส์ไปมุมซ้ายบนจอเพื่อ **หยุดฉุกเฉิน** (PyAutoGUI fail-safe)
- ถ้า template ไม่ตรง ให้ capture ใหม่บนเครื่องที่ใช้งานจริง
- ทดสอบ Excel parser บน Mac ได้ด้วย `python tools/validate_excel.py`
