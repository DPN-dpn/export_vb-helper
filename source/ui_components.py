import tkinter as tk
from tkinter import ttk
import os
from common import REQUIRED_COMPONENT_KEYS
from tkinter import filedialog

class UIComponents:
    def __init__(self, root):
        self.root = root
        self.matcher = None
        self.asset_path_var = tk.StringVar(value="(선택 안 됨)")
        self.mod_path_var = tk.StringVar(value="(선택 안 됨)")
        self.component_widgets = []  # 리스트: 각 컴포넌트의 {key: Combobox} 맵

    def ask_folder(self, title):
        return filedialog.askdirectory(title=title, initialdir=os.getcwd())

    def build_ui(self):
        top = tk.Frame(self.root)
        top.pack(pady=5)

        tk.Button(top, text="에셋 폴더 선택", command=self.matcher.select_asset_folder).pack(side="left", padx=5)
        tk.Label(top, textvariable=self.asset_path_var, width=60, anchor="w").pack(side="left")

        tk.Button(top, text="모드 폴더 선택", command=self.matcher.select_mod_folder).pack(side="left", padx=5)
        tk.Label(top, textvariable=self.mod_path_var, width=60, anchor="w").pack(side="left")

        self.scroll_frame = tk.Frame(self.root)
        self.scroll_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.scroll_frame)
        self.inner_frame = tk.Frame(self.canvas)
        self.scrollbar = tk.Scrollbar(self.scroll_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def display_components(self, components, logger, mod_files_by_type):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.component_widgets.clear()

        for idx, comp in enumerate(components):
            group = tk.LabelFrame(self.inner_frame, text=comp.get("name"))
            group.pack(fill="x", padx=10, pady=5)

            widget_row = {}

            for key in REQUIRED_COMPONENT_KEYS:
                row = tk.Frame(group)
                row.pack(fill="x", pady=2)

                tk.Label(row, text=key, width=12).pack(side="left")

                hash_val = comp.get(key) or ""
                tk.Label(row, text=hash_val, width=15, anchor="w", bg="#f0f0f0").pack(side="left", padx=5)

                # 후보 항목에서 드롭다운 리스트 구성
                candidates = mod_files_by_type.get(key, [])
                selected = tk.StringVar()
                box = ttk.Combobox(row, textvariable=selected, values=candidates, width=80, state="readonly")
                box.pack(side="left", padx=5)

                widget_row[key] = box

            self.component_widgets.append(widget_row)