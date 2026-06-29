# Electronic Parts Counter 🔧

Nhận diện & **đếm linh kiện điện tử** (điện trở, tụ, transistor...) bằng **YOLOv8**,
kèm bộ công cụ **gán nhãn bán tự động** + **train Kaggle GPU miễn phí** + **giao diện**.

> Quy trình: **Gán nhãn → Train → Nhận diện & đếm** — tất cả từ 1 giao diện.

---

## 📑 Mục lục
- [Tải về & Chạy](#-tải-về--chạy)
- [HƯỚNG DẪN SỬ DỤNG CHI TIẾT](#-hướng-dẫn-sử-dụng-chi-tiết)
- [Train trên Kaggle GPU](#️-train-trên-kaggle-gpu-miễn-phí)
- [Chạy bằng GPU (tăng FPS)](#-chạy-bằng-gpu-tăng-fps)
- [Cấu trúc & Mẹo](#-cấu-trúc-dự-án)

---

## 🚀 Tải về & Chạy

**Cần cài sẵn [Python 3.9+](https://www.python.org/downloads/)** (lúc cài nhớ tick *"Add Python to PATH"*).

### Cách 1 — Đơn giản nhất (Windows)
1. Tải code: nút **Code → Download ZIP** trên GitHub → **giải nén**. (Hoặc `git clone https://github.com/phucttp/Electronic-Parts-Counter.git`)
2. Vào thư mục → **nháy đôi `run.bat`**.
   - Lần đầu nó **tự cài thư viện** (đợi vài phút) rồi **mở app**.
   - Các lần sau: nháy đôi là chạy ngay.

### Cách 2 — Bằng lệnh
```bash
git clone https://github.com/phucttp/Electronic-Parts-Counter.git
cd Electronic-Parts-Counter
pip install -r requirements.txt     # hoac nhay doi setup.bat
python m4_gui/app.py
```

---

## 📖 HƯỚNG DẪN SỬ DỤNG CHI TIẾT

### Giao diện chính (bảng điều khiển)

```
┌─ Trạng thái ───────────────────────────┐
│ Số loại: 2 hiện / 2 tổng               │
│   • CAP   100 ảnh |  777 box           │
│   • RES   120 ảnh |  781 box           │
│ Độ chính xác (mAP50): 46% [thấp]       │  ← xanh ≥70% / vàng 50-70% / đỏ <50%
├─ Thao tác ─────────────────────────────┤
│ Nguồn: [../test/vi3.mp4    ] [Chọn ROI]│
│ ☐ Auto-label (gợi ý box)               │
│ [1. Gán nhãn] [2. Import] [3. Train    │
│  Cloud] [4. Train Local] [5. Nhận diện]│
│ [Làm mới] [Quản lý loại] [⚙ Cài đặt]   │
└─────────────────────────────────────────┘
```

### Quy trình đầy đủ A → Z

**Bước 1 — Chọn nguồn**
Gõ vào ô **Nguồn**:
- **`0`** = **webcam** (dùng thật — gán nhãn & nhận diện trực tiếp trên camera). Nếu có nhiều cam, thử `1`, `2`...
- Hoặc đường dẫn **video** (vd `../test/vi3.mp4`) — chỉ để test/demo khi chưa có camera.

> Gán nhãn **trực tiếp trên camera** hoàn toàn được: camera chạy live, bấm **SPACE** để chộp khoảnh khắc muốn gán. (Phím tua `a/d` chỉ có với video.)

**Bước 2 — (Khuyến nghị) Chọn vùng ROI**
Bấm **Chọn vùng ROI** → cửa sổ hiện hình khay → **click trái** vài điểm quanh mép khay (≥3 điểm) → **Lưu**.
ROI giúp auto-label chỉ tìm linh kiện *trong khay*, bỏ tay/bàn.
- Chuột phải / **Hoàn tác**: bỏ điểm cuối · **Xóa hết điểm** · **Chụp lại**: lấy frame khác · **Xóa ROI đã lưu**.

**Bước 3 — Gán nhãn**
Tick **Auto-label** (nếu muốn máy gợi ý box) rồi bấm **1. Gán nhãn** → nhập tên loại (vd `dien_tro`) → cửa sổ gán nhãn mở ra.

| Khi đang phát | Phím |
|---------------|------|
| Đóng băng frame để gán | **SPACE** |
| Tua lùi/tới 15 frame (video) | **a** / **d** |
| Tạm dừng | **p** |
| Bật/tắt gợi ý (auto-label) | **m** |
| Thoát | **q** |

| Khi đã đóng băng | Thao tác |
|------------------|----------|
| Vẽ box | **kéo chuột trái** |
| **Xóa 1 box** | **chuột phải** vào box đó |
| Xóa box vừa vẽ | **u** |
| Xóa hết box | **c** |
| Lưu & qua frame | **ENTER** |
| Bỏ qua frame (không lưu) | **x** |

> ⚠️ **Quan trọng:** trong frame đã chọn, gán **ĐỦ mọi con** của loại đang train (đừng bỏ sót) — YOLO học trên toàn ảnh, bỏ sót = dạy nhầm "vật đó là nền".
> Mục tiêu **~150-180 ảnh/loại**. Mỗi loại = 1 phiên (gõ tên 1 lần).

**Bước 3b — (Tùy chọn) Import data YOLO có sẵn**
Bấm **2. Import** → chọn thư mục chứa `ảnh + .txt + classes.txt` → tự gộp vào dataset.

**Bước 4 — Train**
- **3. Train CLOUD** (khuyên dùng): train trên Kaggle GPU, ~vài phút. Cần cấu hình token (xem bên dưới).
- **4. Train LOCAL**: train trên CPU máy này (chậm ~20-40 phút).
- Train xong, **độ chính xác (mAP50)** tự hiện trong bảng Trạng thái.

**Bước 5 — Nhận diện**
Bấm **5. Nhận diện** → cửa sổ detect hiện box màu (mỗi loại 1 màu) + bảng đếm góc trái.

| Phím trong cửa sổ detect | Tác dụng |
|--------------------------|----------|
| Tăng/giảm ngưỡng tin cậy | **+** / **−** |
| Bật/tắt chữ trên box | **l** |
| Tạm dừng (video) | **p** |
| Thoát | **q** |

> Bảng góc hiện: `FPS | CPU/GPU | conf | tổng` + số lượng mỗi loại.
> Ngưỡng (conf) tùy model: model nhiều class thường dùng **~0.3-0.4**. Dùng `+/-` dò mức đẹp.

### Quản lý loại
Bấm **Quản lý loại**:
- **Ẩn** (xóa mềm): tạm giấu, **giữ data**, hoàn tác được. Train lại sẽ bỏ khỏi model.
- **Xóa hẳn**: xóa luôn ảnh + nhãn của loại (tự dồn id). **Không hoàn tác** (hỏi 2 lần).

### Đọc độ chính xác (mAP50)
Hiện trong bảng Trạng thái sau khi train:
- 🟢 **≥ 70%** — tốt, deploy được
- 🟡 **50-70%** — tạm ổn
- 🔴 **< 50%** — thấp → cần thêm mẫu (GUI tự gợi ý loại nào < 80 ảnh)

---

## ☁️ Train trên Kaggle GPU (miễn phí)

1. Tạo token: [kaggle.com](https://www.kaggle.com) → **Settings → API Tokens → Generate** → copy chuỗi token.
2. Trong GUI: **⚙ Cài đặt Kaggle** → dán **Token** (+ **Username** nếu khác tài khoản) → **Kiểm tra kết nối** → **Lưu**.
3. Bấm **3. Train CLOUD** → tự đẩy data → train GPU T4 → tải `best.pt` về.

> Chi tiết: [`cloud_kaggle/README.md`](cloud_kaggle/README.md).
> Token lưu ở `cloud_kaggle/secrets.json` (đã gitignore — không lộ lên git).

---

## ⚡ Chạy bằng GPU (tăng FPS)

Mặc định chạy **CPU** (FPS ~5-10). Máy có **GPU NVIDIA đời mới** (RTX 20xx/30xx/40xx, GTX 16xx) sẽ **tự động dùng GPU** (FPS 60-150+) — **không cần sửa code**, nhưng phải cài **torch bản CUDA**:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

**Kiểm tra:**
```bash
python -c "import torch; print('GPU:', torch.cuda.is_available())"
```
→ `True` = đang dùng GPU. Cửa sổ detect cũng hiện **GPU/CPU** ở bảng góc.

> Lưu ý: `pip install -r requirements.txt` thường cho **torch CPU-only** → có GPU vẫn chạy CPU đến khi cài torch CUDA như trên. GPU quá cũ (vd 920M) không hỗ trợ.

---

## 📁 Cấu trúc dự án

```
m0_core/      Nền tảng: dataset, class, ROI, metrics, xóa mềm/cứng
m1_annotate/  Gán nhãn (annotate) + auto-label (assist) + import data
m2_train/     Train YOLOv8 (local)
m3_detect/    Nhận diện realtime (màu + đếm + CPU/GPU)
m4_gui/       Giao diện Tkinter (bảng điều khiển + dialog)
cloud_kaggle/ Train trên Kaggle GPU (1 nút)
dataset/      Ảnh + nhãn (chuẩn YOLO) + data.yaml
models/       best.pt (model đã train) + metrics.json
```

## 💡 Mẹo để model chính xác

1. Cố định **1 setup** (khay + ánh sáng + camera) — mọi data quay từ đây.
2. Gán **đủ mọi linh kiện trong frame**, ~150-180 ảnh/loại. Dùng Auto-label + ROI cho nhanh.
3. Train Cloud → xem mAP (≥70% là tốt) → thiếu thì gán thêm.
4. Linh kiện điện tử nhiều loại → nên gán **tất cả loại** xuất hiện trong khay (cả transistor, LED).

## ❓ Lỗi thường gặp

| Lỗi | Cách xử |
|-----|---------|
| Detect không ra gì | Hạ ngưỡng (`-`) về ~0.25-0.3; hoặc model chưa đủ data |
| Train Cloud báo thiếu token | Vào ⚙ Cài đặt Kaggle dán token |
| FPS thấp | Bình thường nếu CPU; cài torch CUDA nếu có GPU |
| mAP thấp (đỏ) | Gán thêm mẫu (đủ mỗi frame), train lại |

---

Thêm loại mới = gán nhãn loại đó + Train lại (YOLO train lại toàn bộ dataset).
`yolov8n.pt` tự tải khi train lần đầu.
