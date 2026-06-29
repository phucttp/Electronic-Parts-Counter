# -*- coding: utf-8 -*-
"""
import_labels.py  (thuộc Module 1 - chuẩn bị dữ liệu)
=====================================================
Nhập một thư mục đã gán nhãn YOLO sẵn (ảnh + .txt cùng tên + classes.txt) vào
dataset của tool. Tự ÁNH XẠ class id nguồn -> id trong data.yaml của mình,
tự chia train/val, đặt tiền tố tên để khỏi đè file cũ.

Dùng:
  python m1_annotate/import_labels.py --src ../img/yoloDataDraft
  python m1_annotate/import_labels.py --src <thu_muc> --check   # chỉ xem, không copy
"""
import sys
import shutil
import argparse
import pathlib

import cv2  # chỉ để xác thực ảnh đọc được

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from m0_core import core  # noqa: E402

IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp")


def read_src_classes(src):
    """Đọc classes.txt nguồn -> list tên theo thứ tự id. Rỗng nếu không có."""
    f = src / "classes.txt"
    if not f.exists():
        return []
    return [ln.strip() for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]


def find_image(txt_path):
    """Tìm ảnh cùng tên với file nhãn."""
    for ext in IMG_EXTS:
        p = txt_path.with_suffix(ext)
        if p.exists():
            return p
    return None


def main():
    core.setup_utf8_console()
    ap = argparse.ArgumentParser(description="Import data YOLO có sẵn vào dataset")
    ap.add_argument("--src", required=True, help="thư mục chứa ảnh + .txt + classes.txt")
    ap.add_argument("--prefix", default="draft", help="tiền tố tên file để tránh đè")
    ap.add_argument("--check", action="store_true", help="chỉ thống kê, không copy")
    args = ap.parse_args()

    src = pathlib.Path(args.src)
    if not src.is_absolute():
        src = (ROOT / args.src).resolve()
    if not src.is_dir():
        print(f"[!] Không thấy thư mục: {src}"); return

    core.ensure_dirs()
    src_classes = read_src_classes(src)
    print(f"[i] Nguồn: {src}")
    print(f"[i] classes.txt nguồn: {src_classes or '(không có -> giữ nguyên id)'}")

    txts = [t for t in sorted(src.glob("*.txt")) if t.name.lower() != "classes.txt"]
    print(f"[i] Tìm thấy {len(txts)} file nhãn.")

    # Dựng bảng ánh xạ id nguồn -> id đích (qua tên class)
    # Nếu không có classes.txt nguồn thì giữ nguyên id (giả định trùng thứ tự).
    id_map = {}
    for sid, name in enumerate(src_classes):
        tid, _ = core.get_or_add_class(name if name != "dt" else "dien_tro")
        id_map[sid] = tid
        print(f"    map class nguồn {sid}('{name}') -> id đích {tid}")

    stats = {"pairs": 0, "no_img": 0, "empty": 0, "boxes": 0, "train": 0, "val": 0}
    idx = core.count_images_of_class(0)  # nối tiếp số đếm để chia train/val ổn định

    for t in txts:
        img_path = find_image(t)
        if img_path is None:
            stats["no_img"] += 1
            continue

        # đọc + ánh xạ lại id từng dòng
        out_lines = []
        for ln in t.read_text(encoding="utf-8").splitlines():
            parts = ln.split()
            if len(parts) < 5:
                continue
            sid = int(float(parts[0]))
            tid = id_map.get(sid, sid)  # không có map thì giữ nguyên
            out_lines.append(" ".join([str(tid)] + parts[1:]))
        stats["boxes"] += len(out_lines)
        if not out_lines:
            stats["empty"] += 1

        if args.check:
            stats["pairs"] += 1
            continue

        # xác thực ảnh đọc được
        if cv2.imread(str(img_path)) is None:
            print(f"    [bỏ] ảnh hỏng: {img_path.name}"); continue

        is_val = (idx % core.VAL_EVERY == 0)
        img_dir = core.IMG_VAL if is_val else core.IMG_TRAIN
        lbl_dir = core.LBL_VAL if is_val else core.LBL_TRAIN
        stem = f"{args.prefix}_{t.stem}"
        shutil.copy(img_path, img_dir / f"{stem}{img_path.suffix.lower()}")
        (lbl_dir / f"{stem}.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        stats["val" if is_val else "train"] += 1
        stats["pairs"] += 1
        idx += 1

    print("\n=== KẾT QUẢ ===")
    print(f"Cặp ảnh+nhãn xử lý : {stats['pairs']}")
    print(f"Nhãn không có ảnh  : {stats['no_img']}")
    print(f"Nhãn rỗng (nền)    : {stats['empty']}")
    print(f"Tổng box           : {stats['boxes']}")
    if not args.check:
        print(f"Copy vào train     : {stats['train']}")
        print(f"Copy vào val       : {stats['val']}")
        print(f"\n[i] Dataset giờ có (dien_tro): "
              f"{core.count_images_of_class(0)} ảnh | {core.count_boxes_of_class(0)} box")
    else:
        print("(chế độ --check: chưa copy gì)")


if __name__ == "__main__":
    main()
