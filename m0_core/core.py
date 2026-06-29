# -*- coding: utf-8 -*-
"""
MODULE 0 - core.py
==================
Nền tảng dùng chung cho cả bộ tool. Đây là "hợp đồng" (contract) duy nhất
mà các module khác phụ thuộc vào. Giữ file này NHỎ và ỔN ĐỊNH.

Nhiệm vụ:
  1. Định nghĩa đường dẫn chuẩn của dataset / models.
  2. Quản lý danh sách class (đọc/ghi data.yaml theo chuẩn YOLO).
  3. Đổi box pixel -> dòng nhãn YOLO (chuẩn hóa 0..1).
  4. Đếm tiến độ số ảnh đã có cho mỗi class.

Các module m1/m2/m3 KHÔNG gọi lẫn nhau; chúng chỉ:
  - đọc/ghi thư mục dataset/ (chuẩn YOLO), và
  - dùng vài hàm tiện ích trong file này.
"""
import sys
from pathlib import Path


# ============================================================
# 0) BẬT UTF-8 CHO CONSOLE (Windows cp1252 không in được tiếng Việt)
#    Mọi module nên gọi core.setup_utf8_console() ngay đầu hàm main().
# ============================================================
def setup_utf8_console():
    """Ép stdout/stderr sang UTF-8 để in tiếng Việt không lỗi trên Windows."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # Python 3.7+
        except (AttributeError, ValueError):
            pass  # môi trường không hỗ trợ thì bỏ qua


# ============================================================
# 1) ĐƯỜNG DẪN CHUẨN
#    core.py nằm ở:  linhkien_tool/m0_core/core.py
#    -> ROOT (gốc project) = thư mục cha của m0_core = linhkien_tool/
# ============================================================
ROOT = Path(__file__).resolve().parent.parent

DATASET = ROOT / "dataset"
IMG_TRAIN = DATASET / "images" / "train"
IMG_VAL = DATASET / "images" / "val"
LBL_TRAIN = DATASET / "labels" / "train"
LBL_VAL = DATASET / "labels" / "val"
DATA_YAML = DATASET / "data.yaml"

MODELS = ROOT / "models"
BEST = MODELS / "best.pt"

# Cứ mỗi VAL_EVERY ảnh thì 1 ảnh đẩy sang tập val (đánh giá), còn lại train.
VAL_EVERY = 5


# ============================================================
# 2) TẠO CÂY THƯ MỤC
# ============================================================
def ensure_dirs():
    """Tạo sẵn toàn bộ thư mục dataset/models nếu chưa có (idempotent)."""
    for d in (IMG_TRAIN, IMG_VAL, LBL_TRAIN, LBL_VAL, MODELS):
        d.mkdir(parents=True, exist_ok=True)


# ============================================================
# 3) QUẢN LÝ DANH SÁCH CLASS (data.yaml)
#    Ghi dạng block list cho dễ đọc:
#        names:
#          - dien_tro
#          - tu
#    nhưng cũng đọc được dạng inline:  names: ['dien_tro', 'tu']
# ============================================================
def load_classes():
    """Đọc danh sách tên class từ data.yaml. Trả về list[str] (rỗng nếu chưa có)."""
    if not DATA_YAML.exists():
        return []
    names = []
    in_names = False
    for line in DATA_YAML.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("names:"):
            in_names = True
            if "[" in s:  # dạng inline
                inside = s[s.index("[") + 1: s.rindex("]")]
                return [x.strip().strip("'\"") for x in inside.split(",") if x.strip()]
            continue
        if in_names:
            if s.startswith("-"):
                names.append(s[1:].strip().strip("'\""))
            elif s and not s.startswith("#"):
                break  # hết khối names
    return names


def save_classes(names):
    """Ghi lại data.yaml với danh sách class hiện tại (chuẩn ultralytics)."""
    ensure_dirs()
    lines = [
        "# Tự sinh bởi linhkien_tool / m0_core - không cần sửa tay.",
        f"path: {DATASET.as_posix()}",
        "train: images/train",
        "val: images/val",
        f"nc: {len(names)}",
        "names:",
    ]
    lines += [f"  - {n}" for n in names]
    DATA_YAML.write_text("\n".join(lines) + "\n", encoding="utf-8")


def get_or_add_class(name):
    """
    Lấy id của class theo tên; nếu chưa có thì THÊM mới (id = cuối danh sách)
    và lưu data.yaml ngay.
    Lưu ý: id phải ỔN ĐỊNH giữa các lần train -> chỉ thêm vào cuối, không sắp xếp lại.
    Trả về (class_id, danh_sach_class_moi).
    """
    names = load_classes()
    if name in names:
        return names.index(name), names
    names.append(name)
    save_classes(names)
    return len(names) - 1, names


# ============================================================
# 4) CHUYỂN BOX -> NHÃN YOLO
# ============================================================
def to_yolo_line(class_id, box, img_w, img_h):
    """
    box = (x, y, w, h) theo PIXEL (góc trên-trái + rộng/cao).
    Trả về 1 dòng nhãn YOLO: "<id> <xc> <yc> <w> <h>" đã chuẩn hóa 0..1.
    """
    x, y, w, h = box
    xc = (x + w / 2) / img_w
    yc = (y + h / 2) / img_h
    ww = w / img_w
    hh = h / img_h
    clamp = lambda v: max(0.0, min(1.0, v))  # kẹp về [0,1] cho an toàn
    return f"{class_id} {clamp(xc):.6f} {clamp(yc):.6f} {clamp(ww):.6f} {clamp(hh):.6f}"


# ============================================================
# 5) ĐẾM TIẾN ĐỘ
# ============================================================
def count_images_of_class(class_id):
    """Đếm số ẢNH (train+val) có chứa class_id -> để hiện tiến độ X/200."""
    ensure_dirs()
    count = 0
    for lbl_dir in (LBL_TRAIN, LBL_VAL):
        for txt in lbl_dir.glob("*.txt"):
            for line in txt.read_text(encoding="utf-8").splitlines():
                parts = line.split()
                if parts and parts[0] == str(class_id):
                    count += 1
                    break  # mỗi ảnh chỉ đếm 1 lần dù có nhiều box
    return count


def count_boxes_of_class(class_id):
    """Đếm tổng số BOX (instance) của class_id trong toàn dataset (train+val).
    Đây mới là con số quan trọng để huấn luyện YOLO."""
    ensure_dirs()
    count = 0
    for lbl_dir in (LBL_TRAIN, LBL_VAL):
        for txt in lbl_dir.glob("*.txt"):
            for line in txt.read_text(encoding="utf-8").splitlines():
                parts = line.split()
                if parts and parts[0] == str(class_id):
                    count += 1  # đếm TỪNG dòng = từng box
    return count


# ============================================================
# 6) XÓA MỀM (soft delete): chỉ ĐÁNH DẤU "ẩn", KHÔNG đụng nhãn gốc.
#    Việc dồn id chỉ xảy ra khi BUILD bản sạch để train.
# ============================================================
import json  # noqa: E402

_IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp")
DISABLED = DATASET / "disabled.json"


def load_disabled():
    """Set tên các loại đang bị ẨN (xóa mềm)."""
    if DISABLED.exists():
        try:
            return set(json.loads(DISABLED.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()


def set_disabled(name, disabled=True):
    """Bật/tắt trạng thái ẩn của 1 loại. KHÔNG đụng nhãn gốc -> hoàn tác được."""
    ensure_dirs()
    d = load_disabled()
    d.add(name) if disabled else d.discard(name)
    DISABLED.write_text(json.dumps(sorted(d), ensure_ascii=False), encoding="utf-8")
    return d


def is_disabled(name):
    return name in load_disabled()


def active_classes():
    """Các loại đang HOẠT ĐỘNG (bỏ loại bị ẩn), giữ thứ tự."""
    dis = load_disabled()
    return [n for n in load_classes() if n not in dis]


def build_clean_dataset(out_root):
    """
    Tạo 'bản sạch' để TRAIN: bỏ box của loại bị ẩn + DỒN id, ghi vào out_root.
    - KHÔNG có loại nào bị ẩn -> trả về thẳng DATASET (khỏi copy, 0 tốn phí).
    - Ảnh chỉ chứa loại bị ẩn -> bỏ. Ảnh còn loại khác -> giữ, sửa id.
    - KHÔNG đụng nhãn gốc trong dataset/.
    Trả về đường dẫn thư mục dùng để train.
    """
    import shutil
    names = load_classes()
    dis = load_disabled()
    if not dis:
        return DATASET                      # không ẩn gì -> dùng trực tiếp

    active = [n for n in names if n not in dis]
    remap = {old: active.index(n) for old, n in enumerate(names) if n in active}

    out_root = Path(out_root)
    for sub in ("images/train", "images/val", "labels/train", "labels/val"):
        (out_root / sub).mkdir(parents=True, exist_ok=True)

    for lbl_dir, img_dir, split in ((LBL_TRAIN, IMG_TRAIN, "train"),
                                    (LBL_VAL, IMG_VAL, "val")):
        for txt in lbl_dir.glob("*.txt"):
            new_lines = []
            for line in txt.read_text(encoding="utf-8").splitlines():
                p = line.split()
                if not p:
                    continue
                cid = int(float(p[0]))
                if cid not in remap:        # box loại bị ẩn -> bỏ
                    continue
                p[0] = str(remap[cid])      # dồn id
                new_lines.append(" ".join(p))
            if not new_lines:               # ảnh chỉ có loại bị ẩn -> bỏ luôn
                continue
            (out_root / "labels" / split / txt.name).write_text(
                "\n".join(new_lines) + "\n", encoding="utf-8")
            for ext in _IMG_EXTS:
                img = img_dir / f"{txt.stem}{ext}"
                if img.exists():
                    shutil.copy(img, out_root / "images" / split / img.name)
                    break

    (out_root / "data.yaml").write_text("\n".join(
        [f"path: {out_root.as_posix()}", "train: images/train", "val: images/val",
         f"nc: {len(active)}", "names:"] + [f"  - {n}" for n in active]) + "\n",
        encoding="utf-8")
    return out_root


# ============================================================
# 7) XÓA HẲN 1 CLASS (xóa data thật - KHÔNG hoàn tác)
# ============================================================
def _clear_caches():
    """Xóa file .cache cũ của ultralytics (nhãn đã đổi -> cache hết đúng)."""
    for c in DATASET.glob("labels/*.cache"):
        try:
            c.unlink()
        except OSError:
            pass


def delete_class(name):
    """
    XÓA HẲN 1 loại khỏi dataset (đụng nhãn gốc, KHÔNG hoàn tác):
      - bỏ mọi box của loại + DỒN id (loại sau tụt xuống 1)
      - ảnh chỉ chứa loại đó -> xóa ảnh + nhãn; ảnh còn loại khác -> giữ, sửa id
      - cập nhật data.yaml + bỏ khỏi danh sách ẩn (nếu có)
    Trả về dict thống kê.
    """
    names = load_classes()
    if name not in names:
        return {"ok": False, "reason": f"Không có loại '{name}'"}
    k = names.index(name)

    boxes_removed = imgs_deleted = labels_rewritten = 0
    for lbl_dir, img_dir in ((LBL_TRAIN, IMG_TRAIN), (LBL_VAL, IMG_VAL)):
        for txt in list(lbl_dir.glob("*.txt")):
            new_lines = []
            for line in txt.read_text(encoding="utf-8").splitlines():
                p = line.split()
                if not p:
                    continue
                cid = int(float(p[0]))
                if cid == k:                       # box của loại bị xóa
                    boxes_removed += 1
                    continue
                if cid > k:                        # dồn id xuống 1
                    p[0] = str(cid - 1)
                new_lines.append(" ".join(p))
            if new_lines:                          # ảnh còn loại khác -> giữ
                txt.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                labels_rewritten += 1
            else:                                  # ảnh chỉ có loại bị xóa -> bỏ
                txt.unlink()
                for ext in _IMG_EXTS:
                    img = img_dir / f"{txt.stem}{ext}"
                    if img.exists():
                        img.unlink()
                        imgs_deleted += 1
                        break

    names.pop(k)
    save_classes(names)
    if name in load_disabled():                    # dọn khỏi danh sách ẩn
        set_disabled(name, False)
    _clear_caches()
    return {
        "ok": True, "name": name, "classes_left": names,
        "boxes_removed": boxes_removed, "imgs_deleted": imgs_deleted,
        "labels_rewritten": labels_rewritten,
    }


# ============================================================
# 8) VÙNG ROI (khoanh khay) - lưu CHUẨN HÓA 0..1 (không phụ thuộc độ phân giải)
# ============================================================
ROI_FILE = DATASET / "roi.json"


def load_roi():
    """Đọc ROI: list [[nx, ny], ...] chuẩn hóa 0..1. Rỗng nếu chưa có."""
    if ROI_FILE.exists():
        try:
            return json.loads(ROI_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_roi(points_norm):
    """Lưu ROI (list [nx, ny] chuẩn hóa 0..1)."""
    ensure_dirs()
    ROI_FILE.write_text(json.dumps(points_norm), encoding="utf-8")


def clear_roi():
    if ROI_FILE.exists():
        ROI_FILE.unlink()


def roi_to_pixels(roi_norm, w, h):
    """Đổi ROI chuẩn hóa -> điểm pixel theo khung w x h."""
    return [(int(nx * w), int(ny * h)) for nx, ny in roi_norm]


# ============================================================
# 9) METRICS: độ chính xác model (mAP50...) đọc từ results.csv của ultralytics
# ============================================================
METRICS_FILE = MODELS / "metrics.json"


def parse_results_csv(csv_path, names=None):
    """Đọc dòng cuối results.csv -> dict {map50, map5095, precision, recall, classes}."""
    import csv as _csv
    csv_path = Path(csv_path)
    out = {"classes": names if names is not None else load_classes()}
    if not csv_path.exists():
        return out
    try:
        rows = list(_csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()))
    except Exception:
        return out
    if not rows:
        return out
    last = rows[-1]

    def col(sub):
        for k, v in last.items():
            if k and sub in k.strip().lower():
                try:
                    return round(float(v), 4)
                except (TypeError, ValueError):
                    return None
        return None

    out.update({
        "map50": col("map50("), "map5095": col("map50-95"),
        "precision": col("precision"), "recall": col("recall"),
    })
    return out


def load_metrics():
    if METRICS_FILE.exists():
        try:
            return json.loads(METRICS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_metrics(d):
    ensure_dirs()
    METRICS_FILE.write_text(json.dumps(d), encoding="utf-8")


# ============================================================
# Chạy trực tiếp file này để TỰ KIỂM TRA (self-test) nhanh.
# ============================================================
if __name__ == "__main__":
    setup_utf8_console()
    print("ROOT     :", ROOT)
    print("DATASET  :", DATASET)
    print("MODELS   :", MODELS)
    ensure_dirs()
    print("[ok] Đã tạo cây thư mục dataset/models.")
    print("Class hiện có:", load_classes())
    # demo convert nhãn: box (100,50,200,80) trên ảnh 1280x720
    print("Demo nhãn YOLO:", to_yolo_line(0, (100, 50, 200, 80), 1280, 720))
