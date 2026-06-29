# -*- coding: utf-8 -*-
"""
MODULE 3 - detect.py
====================
Nhan dien linh kien realtime bang model da train (models/best.pt).
Hien thi: moi loai 1 MAU (khong ve chu tren tung box cho do roi),
kem 1 BANG nho o goc liet ke mau + ten loai + so luong + FPS.
Cua so tu co cho VUA MAN HINH.

NGUON (--source): "0" webcam | "duong/dan/video.mp4"

CHE DO:
  python m3_detect/detect.py --check                 # load model + thu 1 frame
  python m3_detect/detect.py --source ../test/vi2.mp4
  python m3_detect/detect.py --source 0 --conf 0.5

Phim khi chay: q=thoat | p=tam dung | l=bat/tat chu tren box
"""
import sys
import time
import argparse
import pathlib

import cv2

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from m0_core import core  # noqa: E402

IMGSZ = 640  # PHAI khop imgsz luc train

# Bang mau (BGR) phan biet tung loai linh kien
PALETTE = [
    (60, 220, 60), (60, 160, 255), (230, 80, 60), (0, 215, 255),
    (220, 80, 220), (230, 200, 50), (140, 60, 255), (60, 120, 200),
]
FONT = cv2.FONT_HERSHEY_SIMPLEX


def color_for(cls_id):
    return PALETTE[cls_id % len(PALETTE)]


def get_screen_size():
    """Lay kich thuoc man hinh (Windows). Fallback 1366x768."""
    try:
        import ctypes
        u = ctypes.windll.user32
        return u.GetSystemMetrics(0), u.GetSystemMetrics(1)
    except Exception:
        return 1366, 768


def make_fitter():
    """Tra ve ham fit() co dan frame vua trong ~90% man hinh."""
    sw, sh = get_screen_size()
    max_w, max_h = int(sw * 0.9), int(sh * 0.88)

    def fit(frame):
        h, w = frame.shape[:2]
        s = min(max_w / w, max_h / h, 1.0)  # khong phong to qua goc
        if s < 1.0:
            return cv2.resize(frame, (int(w * s), int(h * s)))
        return frame
    return fit


def get_device_tag():
    """Trả về 'GPU' nếu torch thấy CUDA, ngược lại 'CPU'."""
    try:
        import torch
        return "GPU" if torch.cuda.is_available() else "CPU"
    except Exception:
        return "CPU"


def draw_overlay(frame, res, names, fps, conf, show_label, disabled=None, device="CPU"):
    """Ve box theo mau + bang chu thich nho o goc trai-tren.
    Bo qua cac loai trong `disabled` (xoa mem) - khong ve, khong dem."""
    disabled = disabled or set()
    counts = {}
    for b in res.boxes:
        cid = int(b.cls[0])
        if names[cid] in disabled:      # loai bi an -> bo qua
            continue
        counts[cid] = counts.get(cid, 0) + 1
        x1, y1, x2, y2 = map(int, b.xyxy[0])
        col = color_for(cid)
        cv2.rectangle(frame, (x1, y1), (x2, y2), col, 2)
        if show_label:
            cv2.putText(frame, names[cid], (x1, y1 - 4), FONT, 0.4, col, 1, cv2.LINE_AA)

    # --- Bang chu thich (legend) goc trai-tren ---
    present = sorted(counts.keys())
    rows = len(present)
    x, y = 10, 10
    w, lh = 290, 24
    h = lh * (rows + 1) + 12
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

    total = sum(counts.values())
    dev_col = (120, 255, 120) if device == "GPU" else (180, 180, 180)
    cv2.putText(frame, f"FPS {fps:.0f} | {device} | conf {conf:.2f} | tong: {total}",
                (x + 10, y + 20), FONT, 0.5, dev_col, 1, cv2.LINE_AA)
    for i, cid in enumerate(present):
        yy = y + 20 + (i + 1) * lh
        col = color_for(cid)
        cv2.rectangle(frame, (x + 10, yy - 11), (x + 26, yy + 1), col, -1)
        cv2.putText(frame, f"{names[cid]}: {counts[cid]}", (x + 34, yy),
                    FONT, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return frame


def parse_source(src):
    if src.isdigit():
        return int(src), False
    p = pathlib.Path(src)
    if not p.is_absolute():
        p = (ROOT / src).resolve()
    return str(p), True


def load_model(model_path):
    if not pathlib.Path(model_path).exists():
        print(f"[!] Khong thay model: {model_path}")
        print("    -> Train truoc (Module 2 hoac Cloud) de tao best.pt.")
        return None
    try:
        from ultralytics import YOLO
    except ImportError:
        print("[!] Chua cai ultralytics. Chay: pip install ultralytics")
        return None
    return YOLO(str(model_path))


def check_only(model, source):
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[!] Khong mo duoc nguon: {source}"); return False
    ok, frame = cap.read(); cap.release()
    if not ok:
        print(f"[!] Khong doc duoc frame: {source}"); return False
    res = model(frame, imgsz=IMGSZ, verbose=False)[0]
    print(f"[ok] Model + nguon OK. Frame dau phat hien {len(res.boxes)} vat.")
    return True


def main():
    core.setup_utf8_console()
    ap = argparse.ArgumentParser(description="Nhan dien linh kien (Module 3)")
    ap.add_argument("--source", default="0")
    ap.add_argument("--model", default=str(core.BEST))
    ap.add_argument("--conf", type=float, default=0.6)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    model = load_model(args.model)
    if model is None:
        sys.exit(1)
    device = get_device_tag()
    print(f"[i] Model: {args.model}")
    print(f"[i] Class: {model.names}")
    print(f"[i] Thiết bị: {device}" + ("" if device == "GPU"
          else " (cài torch CUDA để chạy GPU nhanh hơn - xem README)"))

    source, is_video = parse_source(args.source)
    if args.check:
        sys.exit(0 if check_only(model, source) else 1)

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[!] Khong mo duoc nguon: {source}"); return

    win = "Detect | q=thoat p=dung l=chu +/-=nguong"
    cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
    fit = make_fitter()
    delay = 25 if is_video else 1
    paused = False
    show_label = False   # mac dinh KHONG ve chu tren box (dung mau + bang goc)
    conf = args.conf     # nguong tin cay (chinh live bang +/-)
    disabled = core.load_disabled()   # loai bi an (xoa mem) -> khong hien
    if disabled:
        print(f"[i] Loai bi an (khong hien): {sorted(disabled)}")
    frame = None

    while True:
        if not paused:
            ok, raw = cap.read()
            if not ok:
                if is_video:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue
                print("[!] Mat tin hieu nguon."); break
            frame = fit(raw)

        t0 = time.time()
        res = model(frame, imgsz=IMGSZ, conf=conf, verbose=False)[0]
        fps = 1.0 / max(time.time() - t0, 1e-6)
        disp = draw_overlay(frame.copy(), res, model.names, fps, conf, show_label, disabled, device)
        cv2.imshow(win, disp)

        key = cv2.waitKey(delay) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('p'):
            paused = not paused
        elif key == ord('l'):
            show_label = not show_label
        elif key in (ord('+'), ord('=')):          # tang nguong -> chinh xac hon
            conf = min(0.95, round(conf + 0.05, 2))
        elif key in (ord('-'), ord('_')):          # giam nguong -> bat nhieu hon
            conf = max(0.05, round(conf - 0.05, 2))

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
