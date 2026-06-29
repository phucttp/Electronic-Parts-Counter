# -*- coding: utf-8 -*-
"""
mock_test.py - Chạy thử Module 0 KHÔNG cần camera.

Giả lập đúng những gì annotate.py sẽ làm:
  - thêm class
  - tạo ảnh giả (numpy) + ghi nhãn YOLO qua core
  - đếm tiến độ X/target
  - in data.yaml + cây thư mục dataset
Cuối cùng TỰ DỌN các file mock để dataset thật vẫn sạch.

Chạy:  python m0_core/mock_test.py
"""
import numpy as np
import cv2

import core  # cùng thư mục -> import trực tiếp được


# Các box giả (x, y, w, h) theo pixel trên ảnh 1280x720, để test convert nhãn
FAKE_BOXES = {
    "dien_tro": [(100, 50, 200, 80), (700, 300, 150, 150)],   # 2 linh kiện/ảnh
    "tu":       [(400, 200, 120, 120)],                       # 1 linh kiện/ảnh
}
SAMPLES_PER_CLASS = 7   # số ảnh giả mỗi loại
IMG_W, IMG_H = 1280, 720


def make_fake_image(seed):
    """Tạo 1 ảnh giả có vài hình chữ nhật cho giống linh kiện trên khay."""
    img = np.full((IMG_H, IMG_W, 3), 40, dtype=np.uint8)  # nền xám tối
    rng = np.random.default_rng(seed)
    color = tuple(int(c) for c in rng.integers(80, 255, size=3))
    cv2.rectangle(img, (100 + seed, 50), (300 + seed, 130), color, -1)
    return img


def save_mock_sample(class_id, boxes, index):
    """Bắt chước annotate.save_sample(): lưu ảnh + nhãn, tên có tiền tố MOCK_."""
    is_val = (index % core.VAL_EVERY == 0)
    img_dir = core.IMG_VAL if is_val else core.IMG_TRAIN
    lbl_dir = core.LBL_VAL if is_val else core.LBL_TRAIN

    stem = f"MOCK_{class_id}_{index:03d}"
    img = make_fake_image(index)
    cv2.imwrite(str(img_dir / f"{stem}.jpg"), img)

    lines = [core.to_yolo_line(class_id, b, IMG_W, IMG_H) for b in boxes]
    (lbl_dir / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return is_val


def cleanup_mock():
    """Xóa mọi file có tiền tố MOCK_ để dataset thật vẫn sạch."""
    n = 0
    for d in (core.IMG_TRAIN, core.IMG_VAL, core.LBL_TRAIN, core.LBL_VAL):
        for f in d.glob("MOCK_*"):
            f.unlink()
            n += 1
    return n


def print_tree():
    """In nhanh số file trong từng thư mục dataset."""
    for label, d in [
        ("images/train", core.IMG_TRAIN), ("images/val", core.IMG_VAL),
        ("labels/train", core.LBL_TRAIN), ("labels/val", core.LBL_VAL),
    ]:
        files = sorted(p.name for p in d.glob("*"))
        print(f"  {label:14s}: {len(files)} file -> {files}")


def main():
    core.setup_utf8_console()
    print("=" * 60)
    print("MOCK TEST - MODULE 0 (core.py)")
    print("=" * 60)

    core.ensure_dirs()
    print("[1] ensure_dirs() OK. ROOT =", core.ROOT)

    # --- Thêm class + lưu ảnh giả ---
    print("\n[2] Thêm class & lưu ảnh giả:")
    for name, boxes in FAKE_BOXES.items():
        class_id, names = core.get_or_add_class(name)
        print(f"    + class '{name}' -> id {class_id} | danh sách: {names}")
        for i in range(SAMPLES_PER_CLASS):
            is_val = save_mock_sample(class_id, boxes, i)
            tag = "val " if is_val else "train"
            print(f"        ảnh {i:02d} [{tag}] | {len(boxes)} box")

    # --- Đếm tiến độ ---
    print("\n[3] Tiến độ count_images_of_class():")
    for name in FAKE_BOXES:
        cid = core.load_classes().index(name)
        print(f"    {name:10s}: {core.count_images_of_class(cid)} ảnh")

    # --- Kiểm tra convert nhãn ---
    print("\n[4] Kiểm tra to_yolo_line() (box 100,50,200,80 trên 1280x720):")
    line = core.to_yolo_line(0, (100, 50, 200, 80), IMG_W, IMG_H)
    print("    ->", line)
    expect = "0 0.156250 0.125000 0.156250 0.111111"
    print("    Khớp kỳ vọng:", "✓" if line == expect else f"✗ (cần {expect})")

    # --- Xem data.yaml ---
    print("\n[5] Nội dung data.yaml:")
    print("-" * 40)
    print(core.DATA_YAML.read_text(encoding="utf-8").rstrip())
    print("-" * 40)

    # --- Cây thư mục ---
    print("\n[6] Cây dataset (gồm file MOCK_ vừa tạo):")
    print_tree()

    # --- Dọn dẹp ---
    removed = cleanup_mock()
    print(f"\n[7] Dọn dẹp: đã xóa {removed} file MOCK_. Dataset thật giờ sạch.")
    print("    (data.yaml + class list được GIỮ lại - đó là cấu hình, không phải data)")
    print("\n[DONE] Module 0 chạy ổn ✓")


if __name__ == "__main__":
    main()
