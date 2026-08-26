# AutoKey

โปรแกรม Auto สำหรับ Express Accounting บน Windows โดยอ่านข้อมูลจาก Excel และกรอก **สมุดรายวันจ่าย (PV)** อัตโนมัติ

**เวอร์ชัน:** ดู `constants/version.py`

## ความต้องการ

- Windows 10/11
- Express Accounting — เปิดอยู่หน้า **Dialog เลือกข้อมูล** ก่อนกดเริ่ม
- จอ 1920×1080, scale 100%

## ดาวน์โหลด Windows (.exe)

1. ไปที่ **Actions** → workflow **Build Windows** → เลือก run ล่าสุด
2. ดาวน์โหลด artifact `AutoKey-windows-…` → ได้ `AutoKey.exe`

## Build Windows

```bash
pip install -r requirements.txt -r requirements-build.txt
pyinstaller --noconfirm AutoKey.spec
```

GitHub Actions: `.github/workflows/build-windows.yml`

## ติดตั้ง (พัฒนา)

```bash
cd AutoKey
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python main.py
```

AutoKey รันบน **Windows + Express Accounting** เท่านั้น — กดเริ่มแล้วจะโฟกัส Express, ส่งคีย์ และจับภาพหน้าจอจริง

## ใช้งาน

1. เปิด Express Accounting และ Login
2. รัน AutoKey → เลือก Excel → กรอกรายละเอียด → กด **เริ่ม**
3. AutoKey โฟกัส Express → ส่งคีย์/จับภาพปุ่ม **ค้นหา** อัตโนมัติ

## โครงสร้าง

```
AutoKey/
├── main.py
├── config.yaml
├── services/          # automation, excel, template click, window focus
├── topics/ka_tam/     # PV workflow
├── ui/                # main window
├── assets/
│   ├── icon/
│   └── templates/     # btn_search.png, btn_ok.png
└── AutoKey.spec
```

## Flow สมุดรายวันจ่าย

1. เมนู `5 > 1 > 2` (บัญชี > ลงประจำวัน > สมุดรายวันจ่าย)
2. F2 สร้างรายการ → กรอกหัวเรื่อง
3. บัญชี `5330-05` + F8 ค้นหา vendor
4. บัญชี `1154-00` + ใบกำกับภาษีซื้อ
5. บัญชี `1111-00` เครดิต
6. F10 บันทึก → วนทำแถวถัดไป

## หมายเหตุ

- ย้ายเมาส์ไปมุมซ้ายบนจอเพื่อ **หยุดฉุกเฉิน** (PyAutoGUI fail-safe)
- Template ต้อง capture บนจอ 1920×1080 scale 100% ที่ใช้งานจริง
- จับภาพปุ่มไม่เจอ → fallback เป็น Tab×2 Enter
