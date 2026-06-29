# -*- coding: utf-8 -*-
"""
status_panel.py - Panel hiển thị trạng thái dataset + ĐỘ CHÍNH XÁC model (mAP).
"""
import tkinter as tk
from tkinter import ttk

from core_bridge import status


class StatusPanel(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text=" Trạng thái ")
        self.box = tk.Text(self, height=7, width=48, relief="flat",
                           background="#f5f5f5", state="disabled", font=("Consolas", 10))
        self.box.pack(padx=8, pady=(8, 4), fill="both", expand=True)
        # Dòng độ chính xác (đổi màu theo mức tốt/ổn/thấp)
        self.acc = tk.Label(self, text="", font=("Segoe UI", 10, "bold"),
                            anchor="w", justify="left")
        self.acc.pack(fill="x", padx=10, pady=(0, 8))
        self._auto_refresh()

    def _auto_refresh(self):
        """Tự cập nhật mỗi 4s -> train xong là mAP hiện ngay, khỏi bấm tay."""
        self.refresh()
        self.after(4000, self._auto_refresh)

    def _sample_hint(self, s):
        low = [name for name, imgs, boxes, hidden in s["per"] if not hidden and imgs < 80]
        return ("\n→ Nên thêm mẫu: " + ", ".join(low) + " (mỗi loại nên ≥80 ảnh)") if low else ""

    def refresh(self):
        s = status.get_status()
        n_active = len(s["classes"]) - len(s["disabled"])
        lines = [f"Số loại: {n_active} hiện / {len(s['classes'])} tổng"]
        if s["per"]:
            for name, imgs, boxes, hidden in s["per"]:
                tag = "  [ẨN]" if hidden else ""
                lines.append(f"   • {name:<12} {imgs:>4} ảnh | {boxes:>5} box{tag}")
        else:
            lines.append("   (chưa có loại nào — hãy gán nhãn)")
        self.box.config(state="normal")
        self.box.delete("1.0", "end")
        self.box.insert("end", "\n".join(lines))
        self.box.config(state="disabled")

        # --- Độ chính xác model ---
        m = s.get("metrics") or {}
        map50 = m.get("map50")
        if not s["has_model"]:
            self.acc.config(text="Model: ✗ Chưa có — hãy train", fg="#c0392b")
        elif map50 is None:
            self.acc.config(text="Model: ✓ có (chưa có số độ chính xác — train lại để cập nhật)",
                            fg="#666")
        else:
            pct = round(map50 * 100)
            if map50 >= 0.70:
                color, tag = "#1e8e3e", "tốt"
            elif map50 >= 0.50:
                color, tag = "#e69500", "tạm ổn"
            else:
                color, tag = "#c0392b", "thấp"
            self.acc.config(text=f"Độ chính xác (mAP50): {pct}%  [{tag}]" + self._sample_hint(s),
                            fg=color)
