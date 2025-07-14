import tkinter as tk
from common import REQUIRED_COMPONENT_KEYS
from tkinter import filedialog
import os

class UIComponents:
    def __init__(self, root):
        self.root = root
        self.matcher = None
        self.component_vars = []
        self.component_paths = []
        self.asset_path_var = tk.StringVar(value="(선택 안 됨)")
        self.mod_path_var = tk.StringVar(value="(선택 안 됨)")

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

    def display_component_sets(self, sets, logger):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        for idx, comp in enumerate(sets):
            group = tk.LabelFrame(self.inner_frame, text=f"컴포넌트 세트 {idx+1}")
            group.pack(fill="x", padx=10, pady=5)

            comp_vars = {}
            comp_paths = {}

            for key in REQUIRED_COMPONENT_KEYS:
                row = tk.Frame(group)
                row.pack(fill="x", pady=2)

                tk.Label(row, text=key, width=12).pack(side="left")
                var = tk.StringVar(value=comp.get(key) or "")
                entry = tk.Entry(row, textvariable=var, width=80)
                entry.pack(side="left", padx=5)

                def picker(k=key, v=var):
                    path = filedialog.askopenfilename(initialdir=os.getcwd())
                    if path:
                        v.set(path)
                        logger.log(f"[수정] {k} → {path}")

                tk.Button(row, text="파일 선택", command=picker).pack(side="right")

                comp_vars[key] = var
                comp_paths[key] = comp.get(key)

            self.component_vars.append(comp_vars)
            self.component_paths.append(comp_paths)