# Electronic Parts Counter 🔧

Nhận diện & **đếm linh kiện điện tử** (điện trở, tụ, transistor...) bằng **YOLOv8**,
kèm bộ công cụ **gán nhãn bán tự động** + **train trên Kaggle GPU miễn phí** + **giao diện**.

> Gán nhãn → Train (cloud/local) → Nhận diện & đếm — tất cả từ 1 giao diện.

---

## ✨ Tính năng

- **Gán nhãn bằng chuột** (Module 1): vẽ box, chuột phải xóa, **auto-label** (model/CV gợi ý box), khoanh **vùng ROI**.
- **Train**: trên **Kaggle GPU T4 (free)** chỉ 1 nút, hoặc **CPU local**.
- **Nhận diện realtime** (Module 3): mỗi loại 1 màu, bảng đếm ở góc, chỉnh ngưỡng live (`+/-`).
- **Quản lý loại**: ẩn (xóa mềm) / xóa hẳn, tự dồn id.
- **Hiển thị độ chính xác** (mAP50) + gợi ý thêm mẫu.

## 🚀 Cài đặt

Cần **Python 3.9+**.

```bash
git clone https://github.com/phucttp/Electronic-Parts-Counter.git
cd Electronic-Parts-Counter
pip install -r requirements.txt        # hoac: nhay doi setup.bat (Windows)
```

## ▶️ Chạy

```bash
python m4_gui/app.py
```

Giao diện gồm: gán nhãn · import data · Train Cloud/Local · nhận diện · quản lý loại · cài đặt Kaggle.

### Hoặc dùng CLI từng module
```bash
python m1_annotate/annotate.py --source 0 --name dien_tro --assist   # gan nhan (webcam)
python m2_train/train.py                                             # train local
python m3_detect/detect.py --source 0                                # nhan dien
```

## ☁️ Train trên Kaggle GPU (miễn phí)

1. Tạo token: kaggle.com → Settings → API Tokens → **Generate** → copy.
2. Trong GUI: **⚙ Cài đặt Kaggle** → dán token → Lưu (hoặc đặt biến `KAGGLE_API_TOKEN`).
3. Bấm **Train CLOUD** → tự đẩy data → train GPU → tải `best.pt` về.

Chi tiết: [`cloud_kaggle/README.md`](cloud_kaggle/README.md).

## 📁 Cấu trúc

```
m0_core/      Nền tảng: dataset, class, ROI, metrics, xóa mềm/cứng
m1_annotate/  Gán nhãn + auto-label (assist) + import data YOLO
m2_train/     Train YOLOv8 (local)
m3_detect/    Nhận diện realtime (màu + đếm)
m4_gui/       Giao diện Tkinter (bảng điều khiển)
cloud_kaggle/ Train trên Kaggle GPU (1 nút)
dataset/      Ảnh + nhãn (chuẩn YOLO) + data.yaml
models/       best.pt (model đã train)
```

## 💡 Quy trình thực tế

1. Cố định **1 setup** (khay + ánh sáng + camera) — mọi data từ đây.
2. Gán **đủ mọi linh kiện trong frame** (~150-180 ảnh/loại). Auto-label + ROI cho nhanh.
3. Train Cloud → xem **mAP50** trong GUI (≥70% là tốt).
4. Nhận diện, chỉnh ngưỡng `+/-` cho hợp.

## 📝 Ghi chú

- `secrets.json` (token Kaggle) **không** được commit (đã gitignore).
- `yolov8n.pt` tự tải khi train lần đầu.
- Thêm loại mới = gán nhãn + train lại (YOLO train lại toàn bộ).
