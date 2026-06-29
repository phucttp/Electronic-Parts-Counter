# -*- coding: utf-8 -*-
"""
MODULE 1 - annotate.py
======================
Gán nhãn BÁN TỰ ĐỘNG bằng chuột. Mỗi PHIÊN = 1 loại linh kiện.
Mốc tiến độ theo SỐ ẢNH (frame đa dạng); số box hiển thị kèm tham khảo.
Tiện ích UI (chuột/vẽ/lưu) ở annotate_ui.py; file này lo điều phối + vòng lặp.

NGUỒN (--source): "0" webcam | "duong/dan/vi.mp4" video.

PHÍM:
  Đang phát:   SPACE=đóng băng | a/d=tua | p=tạm dừng | m=bật/tắt gợi ý | q=thoát
  Đóng băng:   kéo chuột=vẽ box | chuột phải=xóa box | ENTER=lưu | u=xóa cuối |
               c=xóa hết | x=bỏ qua frame

AUTO-LABEL (--assist): mode 'cv' (tách biên trong ROI) hoặc 'model' (YOLO gợi ý).
ROI khoanh khay lấy từ GUI (lưu sẵn) -> gợi ý chỉ tìm trong khay.

VÍ DỤ:
  python m1_annotate/annotate.py --source ../test/vi3.mp4 --name dien_tro --assist
  python m1_annotate/annotate.py --check --source ../test/vi2.mp4
"""
import sys
import argparse
import pathlib

import cv2
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from m0_core import core  # noqa: E402
import assist  # noqa: E402  (cùng thư mục m1_annotate)
from annotate_ui import (on_mouse, fit, draw_overlay, save_sample,  # noqa: E402
                         parse_source, check_only)


def main():
    core.setup_utf8_console()
    ap = argparse.ArgumentParser(description="Gán nhãn linh kiện (Module 1)")
    ap.add_argument("--source", default="0")
    ap.add_argument("--name", default=None)
    ap.add_argument("--target", type=int, default=125, help="số ẢNH mục tiêu/loại")
    ap.add_argument("--assist", action="store_true", help="bật gợi ý box sẵn (auto-label)")
    ap.add_argument("--assist-mode", choices=["model", "cv"], default="cv",
                    help="kiểu gợi ý: cv (tách biên theo diện tích) hoặc model (YOLO)")
    ap.add_argument("--assist-conf", type=float, default=0.2, help="ngưỡng gợi ý model")
    ap.add_argument("--model", default=str(core.BEST), help="model dùng để gợi ý (mode=model)")
    ap.add_argument("--cv-min", type=int, default=400, help="diện tích box nhỏ nhất (mode=cv)")
    ap.add_argument("--cv-max", type=int, default=40000, help="diện tích box lớn nhất (mode=cv)")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    source, is_video = parse_source(args.source)
    if args.check:
        sys.exit(0 if check_only(source) else 1)

    class_name = args.name or input("Nhập tên loại linh kiện (vd dien_tro): ").strip()
    if not class_name:
        print("Tên rỗng, thoát."); return
    class_id, names = core.get_or_add_class(class_name)

    # state dùng chung giữa vòng lặp + callback chuột
    st = {
        "frozen": False, "drawing": False, "p0": (0, 0), "p1": (0, 0),
        "boxes": [],                                  # box của frame đang đóng băng
        "saved_imgs": core.count_images_of_class(class_id),  # ẢNH đã lưu (mốc chính)
        "saved_boxes": core.count_boxes_of_class(class_id),  # box đã lưu (tham khảo)
    }
    print(f"[i] Loại '{class_name}' = id {class_id}. "
          f"Đã có {st['saved_imgs']}/{args.target} ảnh ({st['saved_boxes']} box).")
    print(f"[i] Class hiện tại: {names}")

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[!] Không mở được nguồn: {source}"); return

    win = "Annotate"
    cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(win, on_mouse, st)

    frame = None          # frame hiện đang phát (đã fit)
    frozen_img = None     # ảnh đóng băng để gán nhãn
    delay = 25 if is_video else 1
    paused = False
    assist_on = args.assist                                          # bật/tắt gợi ý
    assist_model = (assist.load_model(args.model)
                    if args.assist and args.assist_mode == "model" else None)
    roi_norm = core.load_roi()                                       # vùng khay (chuẩn hóa)
    if len(roi_norm) >= 3:
        print(f"[i] Có vùng ROI ({len(roi_norm)} điểm) -> gợi ý chỉ tìm trong khay.")

    while True:
        if not st["frozen"]:
            if not paused:
                ok, raw = cap.read()
                if not ok:
                    if is_video:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue
                    print("[!] Mất tín hiệu nguồn."); break
                frame = fit(raw)
            base = frame
        else:
            base = frozen_img

        if base is None:
            continue
        disp = draw_overlay(base, st, class_name, args.target)
        if len(roi_norm) >= 3:                      # vẽ vùng ROI (khay)
            hh, ww = base.shape[:2]
            pts = np.array(core.roi_to_pixels(roi_norm, ww, hh), np.int32)
            cv2.polylines(disp, [pts], True, (255, 150, 0), 1, cv2.LINE_AA)
        if not st["frozen"]:
            tag = "BAT" if assist_on else "TAT"
            col = (120, 255, 120) if assist_on else (160, 160, 160)
            cv2.putText(disp, f"m=goi y ({tag})", (15, 102),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1, cv2.LINE_AA)
        cv2.imshow(win, disp)
        key = cv2.waitKey(delay) & 0xFF

        if key == ord('q'):
            break

        # ----- ĐANG PHÁT -----
        if not st["frozen"]:
            if key == 32:                      # SPACE -> đóng băng
                frozen_img = frame.copy()
                st["frozen"] = True
                if assist_on and (assist_model is not None or args.assist_mode == "cv"):
                    h0, w0 = frozen_img.shape[:2]
                    roi_px = core.roi_to_pixels(roi_norm, w0, h0) if len(roi_norm) >= 3 else None
                    st["boxes"] = assist.propose(frozen_img, args.assist_mode, assist_model,
                                                 args.assist_conf, args.cv_min, args.cv_max, roi_px)
                    print(f"[assist] Gợi ý {len(st['boxes'])} box ({args.assist_mode}) "
                          "-> chuột phải xóa cái sai rồi ENTER.")
                else:
                    st["boxes"] = []
            elif key == ord('p'):
                paused = not paused
            elif is_video and key in (ord('a'), ord('d')):
                pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
                cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, pos + (15 if key == ord('d') else -15)))
                paused = False
            elif key == ord('m'):              # bật/tắt gợi ý (auto-label)
                assist_on = not assist_on
                if assist_on and args.assist_mode == "model" and assist_model is None:
                    assist_model = assist.load_model(args.model)
                    if assist_model is None:
                        assist_on = False
                print(f"[assist] Gợi ý ({args.assist_mode}): {'BẬT' if assist_on else 'TẮT'}")
        # ----- ĐANG ĐÓNG BĂNG -----
        else:
            if key == ord('u') and st["boxes"]:        # xóa box cuối
                st["boxes"].pop()
            elif key == ord('c'):                      # xóa hết
                st["boxes"] = []
            elif key == ord('x'):                      # bỏ qua frame, không lưu
                st["frozen"] = False; st["boxes"] = []
            elif key in (13, 10):                      # ENTER -> lưu & tiếp
                if st["boxes"]:
                    is_val = save_sample(frozen_img, st["boxes"], class_id, st["saved_imgs"])
                    st["saved_imgs"] += 1
                    st["saved_boxes"] += len(st["boxes"])
                    print(f"[+] Lưu ảnh ({'val' if is_val else 'train'}) | "
                          f"+{len(st['boxes'])} box | tổng {st['saved_imgs']}/{args.target} ảnh")
                    if st["saved_imgs"] >= args.target:
                        print(f"[✓] Đủ {args.target} ảnh cho '{class_name}'. Có thể thoát rồi train.")
                else:
                    print("[i] Frame chưa có box -> bỏ qua (dùng 'x' nếu muốn skip).")
                st["frozen"] = False; st["boxes"] = []

    cap.release()
    cv2.destroyAllWindows()
    print(f"[done] '{class_name}': {core.count_boxes_of_class(class_id)} box "
          f"trong {core.count_images_of_class(class_id)} ảnh.")


if __name__ == "__main__":
    main()
