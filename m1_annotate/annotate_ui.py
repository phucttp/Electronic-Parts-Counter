# -*- coding: utf-8 -*-
"""
annotate_ui.py - Tiện ích UI cho annotate: chuột, vẽ HUD, fit khung, lưu mẫu.
Tách khỏi annotate.py cho gọn; annotate.py giữ phần điều phối + vòng lặp.
"""
import sys
import time
import pathlib

import cv2

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from m0_core import core  # noqa: E402

DISPLAY_W = 1280  # bề ngang cửa sổ hiển thị (ảnh to co về đây; lưu luôn cỡ này)


def on_mouse(event, x, y, flags, st):
    """Chuột: kéo trái vẽ box, chuột phải xóa box tại chỗ click (chỉ khi đóng băng)."""
    if not st["frozen"]:
        return
    if event == cv2.EVENT_LBUTTONDOWN:
        st["drawing"] = True
        st["p0"] = (x, y)
        st["p1"] = (x, y)
    elif event == cv2.EVENT_MOUSEMOVE and st["drawing"]:
        st["p1"] = (x, y)
    elif event == cv2.EVENT_LBUTTONUP and st["drawing"]:
        st["drawing"] = False
        (x0, y0), (x1, y1) = st["p0"], (x, y)
        bx, by = min(x0, x1), min(y0, y1)
        bw, bh = abs(x1 - x0), abs(y1 - y0)
        if bw > 3 and bh > 3:                     # bỏ qua click lỡ (box quá nhỏ)
            st["boxes"].append((bx, by, bw, bh))
    elif event == cv2.EVENT_RBUTTONDOWN:          # CHUỘT PHẢI -> xóa box tại chỗ click
        hit, smallest = None, None                # ưu tiên box nhỏ nhất chứa điểm
        for i, (bx, by, bw, bh) in enumerate(st["boxes"]):
            if bx <= x <= bx + bw and by <= y <= by + bh:
                area = bw * bh
                if smallest is None or area < smallest:
                    smallest, hit = area, i
        if hit is not None:
            st["boxes"].pop(hit)


def fit(frame):
    """Co frame về bề ngang DISPLAY_W để vừa màn hình + toạ độ chuột khớp 1:1."""
    h, w = frame.shape[:2]
    if w <= DISPLAY_W:
        return frame
    s = DISPLAY_W / w
    return cv2.resize(frame, (DISPLAY_W, int(h * s)))


def draw_overlay(base, st, class_name, target):
    """Vẽ HUD + các box hiện có lên 1 bản copy để hiển thị."""
    disp = base.copy()
    for i, (x, y, w, h) in enumerate(st["boxes"], 1):
        cv2.rectangle(disp, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(disp, str(i), (x + 3, y + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    if st["drawing"]:
        cv2.rectangle(disp, st["p0"], st["p1"], (0, 200, 255), 1)

    boxes_now = st["saved_boxes"] + len(st["boxes"])
    cv2.putText(disp, f"{class_name}: {st['saved_imgs']}/{target} anh  ({boxes_now} box)",
                (15, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 255, 0), 2)
    if st["frozen"]:
        hud = f"[DONG BANG] box: {len(st['boxes'])} | ENTER=luu  chuot phai=xoa box  "\
              "u=xoa cuoi  c=xoa het  x=bo qua"
        cv2.putText(disp, hud, (15, 72),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
    else:
        cv2.putText(disp, "SPACE=dong bang  a/d=tua  p=dung  q=thoat", (15, 72),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
    return disp


def save_sample(frame, boxes, class_id, index):
    """Lưu 1 ảnh + nhãn YOLO. Chia train/val theo core.VAL_EVERY."""
    h, w = frame.shape[:2]
    is_val = (index % core.VAL_EVERY == 0)
    img_dir = core.IMG_VAL if is_val else core.IMG_TRAIN
    lbl_dir = core.LBL_VAL if is_val else core.LBL_TRAIN
    stem = f"{class_id}_{int(time.time() * 1000)}"
    cv2.imwrite(str(img_dir / f"{stem}.jpg"), frame)
    lines = [core.to_yolo_line(class_id, b, w, h) for b in boxes]
    (lbl_dir / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return is_val


def parse_source(src):
    """'0' -> webcam 0; ngược lại là đường dẫn video. Trả về (nguồn, is_video)."""
    if src.isdigit():
        return int(src), False
    p = pathlib.Path(src)
    if not p.is_absolute():
        p = (ROOT / src).resolve()
    return str(p), True


def check_only(source):
    """Chỉ mở nguồn + đọc 1 frame rồi thoát (không GUI)."""
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[!] Không mở được nguồn: {source}"); return False
    ok, frame = cap.read(); cap.release()
    if not ok:
        print(f"[!] Mở được nhưng không đọc được frame: {source}"); return False
    h, w = frame.shape[:2]
    print(f"[ok] Nguồn hợp lệ: {source} | frame {w}x{h}"); return True
