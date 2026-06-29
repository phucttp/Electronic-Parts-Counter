# -*- coding: utf-8 -*-
"""
action_panel.py - Panel cac nut thao tac (goi module qua runner).
"""
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog, messagebox

from core_bridge import runner


class ActionPanel(ttk.LabelFrame):
    def __init__(self, master, on_change=None):
        super().__init__(master, text=" Thao tác ")
        self.on_change = on_change

        # --- O nhap Nguon (dung chung cho gan nhan + detect) ---
        row = ttk.Frame(self)
        row.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Label(row, text="Nguồn:").pack(side="left")
        self.source = tk.StringVar(value="../test/vi2.mp4")
        ttk.Entry(row, textvariable=self.source).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Label(self, text="(webcam = 0, hoặc đường dẫn video)",
                  foreground="#888").pack(anchor="w", padx=10)

        # --- Auto-label: gợi ý box sẵn khi gán + chọn vùng ROI ---
        rowa = ttk.Frame(self)
        rowa.pack(fill="x", padx=10, pady=(2, 0))
        self.assist = tk.BooleanVar(value=False)
        ttk.Checkbutton(rowa, text="Auto-label (gợi ý box — đỡ kéo tay)",
                        variable=self.assist).pack(side="left")
        ttk.Button(rowa, text="Chọn vùng ROI", command=self.pick_roi).pack(side="right")

        # --- Cac nut ---
        self._btn("1.  Gán nhãn  (video / webcam)", self.annotate)
        self._btn("2.  Import data có sẵn (YOLO)", self.import_data)
        ttk.Separator(self).pack(fill="x", padx=8, pady=4)
        self._btn("3.  Train CLOUD  (Kaggle GPU — nhanh)", self.train_cloud)
        self._btn("4.  Train LOCAL  (CPU máy này — chậm)", self.train_local)
        ttk.Separator(self).pack(fill="x", padx=8, pady=4)
        self._btn("5.  Nhận diện  (detect)", self.detect)

    def _btn(self, text, cmd):
        ttk.Button(self, text=text, command=cmd).pack(fill="x", padx=8, pady=3, ipady=3)

    def _maybe_refresh(self, ms=1500):
        if self.on_change:
            self.after(ms, self.on_change)

    # --- Handlers ---
    def annotate(self):
        name = simpledialog.askstring("Gán nhãn", "Tên loại linh kiện (vd dien_tro):")
        if not name:
            return
        runner.run_annotate(self.source.get().strip(), name.strip(), assist=self.assist.get())
        self._maybe_refresh(2000)

    def import_data(self):
        folder = filedialog.askdirectory(title="Chọn thư mục YOLO (ảnh + .txt + classes.txt)")
        if not folder:
            return
        runner.run_import(folder)
        self._maybe_refresh(3000)

    def train_cloud(self):
        if not runner.has_kaggle_token():
            if messagebox.askyesno("Chưa có token Kaggle",
                                   "Chưa cấu hình token Kaggle.\nMở Cài đặt để nhập bây giờ?"):
                from views.settings_dialog import open_settings
                open_settings(self.winfo_toplevel())
            return
        if messagebox.askyesno("Train Cloud",
                               "Đẩy dataset lên Kaggle + train trên GPU?"):
            runner.run_train_cloud()

    def train_local(self):
        if messagebox.askyesno("Train Local",
                               "Train trên CPU máy này?\n(Lâu ~20-40 phút, quạt sẽ kêu 😅)"):
            runner.run_train_local()

    def detect(self):
        runner.run_detect(self.source.get().strip())

    def pick_roi(self):
        from views.roi_dialog import open_roi
        open_roi(self.winfo_toplevel(), self.source.get().strip())
