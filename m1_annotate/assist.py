# -*- coding: utf-8 -*-
"""
assist.py - Gợi ý box tự động (auto-label) để đỡ kéo tay khi gán nhãn.

Chiến lược hiện có: dùng model YOLO (best.pt) đề xuất box — CLASS-AGNOSTIC
(lấy mọi vật, bỏ qua loại dự đoán) vì trong 1 phiên mọi box = loại đang chọn.

Mở rộng sau: thêm hàm propose_* khác (CV tách nền, theo biên dạng linh kiện...)
rồi cho annotate chọn chiến lược — không phải sửa annotate nhiều.
"""
import pathlib


def load_model(model_path):
    """Load YOLO model làm 'mồi' box. None nếu thiếu file / chưa cài ultralytics."""
    if not pathlib.Path(model_path).exists():
        print(f"[assist] Không thấy model {model_path} -> tắt gợi ý (gán tay).")
        return None
    try:
        from ultralytics import YOLO
    except ImportError:
        print("[assist] Chưa cài ultralytics -> tắt gợi ý.")
        return None
    print(f"[assist] Dùng model gợi ý: {model_path}")
    return YOLO(str(model_path))


def propose_boxes(model, frame, conf=0.2, imgsz=640):
    """
    Chạy model trên frame -> list box (x, y, w, h) pixel (CLASS-AGNOSTIC).
    Ngưỡng thấp để đề xuất nhiều, user xóa bớt cái sai (nhanh hơn vẽ từ đầu).
    """
    if model is None:
        return []
    res = model(frame, imgsz=imgsz, conf=conf, verbose=False)[0]
    boxes = []
    for b in res.boxes:
        x1, y1, x2, y2 = (int(v) for v in b.xyxy[0])
        w, h = x2 - x1, y2 - y1
        if w > 3 and h > 3:
            boxes.append((x1, y1, w, h))
    return boxes


def propose_boxes_cv(frame, min_area=300, max_area=40000, roi=None):
    """
    Đề xuất box bằng XỬ LÝ ẢNH (không cần model): tách vật sẫm trên nền khay sáng.
    roi = list điểm [(x,y),...] khoanh vùng khay -> CHỈ tìm trong đó (bỏ tay/bàn/viền).
    Otsu tính RIÊNG trong ROI + MORPH_OPEN để bỏ dây chân -> tách thân linh kiện.
    """
    import cv2
    import numpy as np

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    mask = None
    if roi is not None and len(roi) >= 3:
        mask = np.zeros(gray.shape, np.uint8)
        cv2.fillPoly(mask, [np.array(roi, np.int32)], 255)
        thr, _ = cv2.threshold(gray[mask > 0], 0, 255,
                               cv2.THRESH_BINARY + cv2.THRESH_OTSU)  # Otsu trong ROI
        _, th = cv2.threshold(gray, thr, 255, cv2.THRESH_BINARY_INV)
        th = cv2.bitwise_and(th, mask)
    else:
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    k = np.ones((3, 3), np.uint8)
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, k, iterations=2)    # bỏ dây chân mảnh
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, k, iterations=1)

    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if min_area <= w * h <= max_area and w > 4 and h > 4:
            boxes.append((x, y, w, h))
    return boxes


def _in_roi(box, roi):
    """Tâm box có nằm trong polygon roi không."""
    import cv2
    import numpy as np
    cx, cy = box[0] + box[2] / 2, box[1] + box[3] / 2
    return cv2.pointPolygonTest(np.array(roi, np.int32), (cx, cy), False) >= 0


def propose(frame, mode="model", model=None, conf=0.2, cv_min=300, cv_max=40000, roi=None):
    """Bộ điều phối gợi ý. 'cv' (xử lý ảnh) hoặc 'model' (YOLO). roi lọc theo vùng khay."""
    if mode == "cv":
        return propose_boxes_cv(frame, cv_min, cv_max, roi)
    boxes = propose_boxes(model, frame, conf)
    if roi and len(roi) >= 3:                      # model: lọc box ngoài ROI
        boxes = [b for b in boxes if _in_roi(b, roi)]
    return boxes
