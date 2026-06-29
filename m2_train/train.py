# -*- coding: utf-8 -*-
"""
MODULE 2 - train.py
===================
Huấn luyện YOLOv8n trên TOÀN BỘ dataset đã gán nhãn (chuẩn YOLO trong dataset/).

Nguyên tắc quan trọng:
  • Thêm linh kiện mới -> train LẠI trên cả data cũ + mới (YOLO không "thêm 1 class"
    riêng được; train mỗi data mới sẽ quên class cũ). Nên KHÔNG xóa dataset.
  • Máy này CPU-only (GPU 920M quá cũ, không dùng được) -> device='cpu'.

CHẾ ĐỘ:
  python m2_train/train.py --check          # chỉ kiểm tra dataset, không train
  python m2_train/train.py --epochs 3       # smoke test nhanh (xem pipeline chạy)
  python m2_train/train.py                   # train thật (mặc định 80 epoch)

Sau khi xong: model tốt nhất được copy về models/best.pt cho Module 3 dùng.
"""
import sys
import argparse
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from m0_core import core  # noqa: E402

# Mặc định train thật
DEF_EPOCHS = 100           # đủ data (175 ảnh) -> ~vài chục epoch là hội tụ; early-stop lo phần dư
DEF_PATIENCE = 25          # dừng sớm nếu 25 epoch không cải thiện
DEF_IMGSZ = 640            # linh kiện nhỏ & dày -> cần ảnh to mới thấy (320 quá nhỏ)
BASE_MODEL = "yolov8n.pt"  # nano; tải tự động lần đầu (~6MB)
DEVICE = "cpu"


def dataset_summary():
    """Thu thập thống kê dataset: class, số ảnh, số box mỗi loại."""
    classes = core.load_classes()
    n_train = len(list(core.LBL_TRAIN.glob("*.txt")))
    n_val = len(list(core.LBL_VAL.glob("*.txt")))
    per_class = {
        name: (core.count_images_of_class(i), core.count_boxes_of_class(i))
        for i, name in enumerate(classes)
    }
    return classes, n_train, n_val, per_class


def print_summary():
    classes, n_train, n_val, per_class = dataset_summary()
    print("=" * 56)
    print("KIỂM TRA DATASET")
    print("=" * 56)
    print(f"data.yaml : {core.DATA_YAML}")
    print(f"Số class  : {len(classes)} -> {classes}")
    print(f"Ảnh train : {n_train} | Ảnh val : {n_val}")
    print("Chi tiết mỗi loại (ảnh / box):")
    for name, (imgs, boxes) in per_class.items():
        print(f"   - {name:12s}: {imgs:4d} ảnh | {boxes:4d} box")
    # cảnh báo điều kiện tối thiểu
    ok = True
    if len(classes) == 0:
        print("[!] Chưa có class nào."); ok = False
    if n_train == 0:
        print("[!] Chưa có ảnh train. Gán nhãn bằng Module 1 trước."); ok = False
    if n_val == 0:
        print("[~] Chưa có ảnh val -> nên gán thêm vài frame để đánh giá "
              "(cứ mỗi 5 ảnh có 1 ảnh val).")
    if ok:
        print("[ok] Dataset sẵn sàng để train.")
    return ok


def main():
    core.setup_utf8_console()
    ap = argparse.ArgumentParser(description="Huấn luyện YOLOv8n (Module 2)")
    ap.add_argument("--check", action="store_true", help="chỉ kiểm tra dataset rồi thoát")
    ap.add_argument("--epochs", type=int, default=DEF_EPOCHS)
    ap.add_argument("--patience", type=int, default=DEF_PATIENCE)
    ap.add_argument("--imgsz", type=int, default=DEF_IMGSZ)
    ap.add_argument("--device", default=DEVICE, help="'cpu' hoặc '0' nếu có GPU CUDA")
    args = ap.parse_args()

    core.ensure_dirs()
    ready = print_summary()
    if args.check:
        sys.exit(0 if ready else 1)
    if not ready:
        print("[x] Dataset chưa sẵn sàng -> dừng. (Chạy --check để xem thiếu gì.)")
        return

    print(f"\n[i] Bắt đầu train: epochs={args.epochs}, imgsz={args.imgsz}, device={args.device}")
    if args.device == "cpu":
        print("[i] CPU-only nên sẽ lâu (~15-40 phút tùy số ảnh). Cứ để chạy nền.")

    try:
        from ultralytics import YOLO
    except ImportError:
        print("[!] Chưa cài ultralytics. Chạy: pip install ultralytics"); return

    # Xóa mềm: build bản sạch (bỏ loại bị ẩn + dồn id) -> train trên bản đó.
    # Nếu không ẩn gì, hàm trả về DATASET gốc nên 0 tốn phí.
    clean_root = core.build_clean_dataset(core.ROOT / "_train_view")
    data_yaml = clean_root / "data.yaml"
    if core.load_disabled():
        print(f"[i] Có loại bị ẩn {sorted(core.load_disabled())} -> train trên bản sạch.")

    model = YOLO(BASE_MODEL)
    model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        device=args.device,
        project=str(core.MODELS),
        name="train",
        exist_ok=True,
        patience=args.patience,   # dừng sớm nếu không cải thiện
        # Augmentation: mặc định ultralytics (mosaic/lật ngang/đổi màu/scale/dịch)
        # đã đủ. KHÔNG bật xoay mạnh (degrees) vì linh kiện scattered ĐÃ đủ góc, mà
        # xoay mạnh trên data ít làm model KÉM TỰ TIN (conf tụt). Chỉ lật nhẹ:
        flipud=0.2,
    )

    # Lưu độ chính xác (mAP...) để GUI hiển thị
    metrics = core.parse_results_csv(core.MODELS / "train" / "results.csv",
                                     core.active_classes())
    core.save_metrics(metrics)
    print(f"[i] Độ chính xác: mAP50={metrics.get('map50')} | "
          f"P={metrics.get('precision')} R={metrics.get('recall')}")

    best_src = core.MODELS / "train" / "weights" / "best.pt"
    if best_src.exists():
        shutil.copy(best_src, core.BEST)
        print(f"[✓] Đã lưu model: {core.BEST}")
        print("    -> Chạy Module 3 (detect) để nhận diện.")
    else:
        print(f"[!] Không thấy {best_src}. Xem log train phía trên.")


if __name__ == "__main__":
    main()
