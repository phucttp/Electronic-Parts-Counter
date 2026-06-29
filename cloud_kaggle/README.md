# Train trên Kaggle GPU (free) từ desktop

Train YOLO trên GPU T4 miễn phí của Kaggle, điều khiển **hoàn toàn bằng lệnh từ máy**.
Chỉ bước lấy token là phải mở web **1 lần duy nhất**.

```
[máy bạn]  dataset/  ──push──>  [Kaggle GPU T4]  ──train──>  best.pt  ──pull──>  [máy bạn] models/best.pt
            run_kaggle.ps1                train_kernel.py
```

---

## A. Cài 1 lần (one-time)

### 1. Cài Kaggle CLI
```powershell
pip install kaggle
```

### 2. Lấy API token (bước web DUY NHẤT)
1. Vào https://www.kaggle.com → đăng ký/đăng nhập.
2. Avatar góc phải → **Settings** → mục **API** → **Create New Token**.
3. Tải về file `kaggle.json`.
4. Chép vào: `C:\Users\<TenWindows>\.kaggle\kaggle.json`
   ```powershell
   mkdir $env:USERPROFILE\.kaggle -Force
   move $HOME\Downloads\kaggle.json $env:USERPROFILE\.kaggle\
   ```

### 3. Kiểm tra
```powershell
kaggle datasets list   # ra danh sách là OK
```
> `KaggleUser` = tên đăng nhập Kaggle của bạn (xem trong URL profile: kaggle.com/**ten_nay**).

---

## B. Mỗi lần muốn train (sau khi thêm/sửa data)

Chỉ 1 lệnh — tự đẩy data, train GPU, tải `best.pt` về `models/`:
```powershell
cd c:\tai_lieu_hoc\myproject\kiemSoatLinhKien\linhkien_tool
.\cloud_kaggle\run_kaggle.ps1 -KaggleUser TEN_KAGGLE_CUA_BAN
```

Thêm ghi chú phiên bản dataset:
```powershell
.\cloud_kaggle\run_kaggle.ps1 -KaggleUser ten -Message "them class tu_gom"
```

Đẩy xong không chờ (tự xem trên web Kaggle, tải sau):
```powershell
.\cloud_kaggle\run_kaggle.ps1 -KaggleUser ten -NoWait
```

Train xong → `models\best.pt` sẵn sàng. Chạy detect như thường:
```powershell
python m3_detect\detect.py --source ../test/vi2.mp4
```

---

## C. Các file trong folder này
| File | Vai trò |
|------|---------|
| `train_kernel.py` | Code chạy TRÊN GPU Kaggle (train + xuất best.pt). Sửa epochs/imgsz ở đây. |
| `run_kaggle.ps1` | Orchestrator "1 nút": push data → train → pull weights. |
| `kernel-metadata.json` | Tự sinh bởi script (cấu hình kernel: GPU, internet, dataset nguồn). |
| `README.md` | File này. |

## D. Hướng tới phần mềm tự động
`run_kaggle.ps1` là điểm tích hợp: phần mềm tương lai của bạn chỉ cần gọi
```
powershell -File run_kaggle.ps1 -KaggleUser <user>
```
là có nút "Train trên cloud". Có thể bắt exit code / parse output để báo tiến độ.

## E. Lỗi thường gặp
- `403 / 401`: sai token → kiểm tra `kaggle.json` đúng chỗ.
- `enable_internet` bị tắt: kernel không pip install được → đã bật sẵn trong metadata.
- Lần đầu chạy kernel cần **verify phone** trên Kaggle để được dùng GPU + Internet (yêu cầu 1 lần của Kaggle).
- Dataset to → lần đẩy đầu hơi lâu (upload ảnh).
```
