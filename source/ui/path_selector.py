import tkinter as tk
from tkinter import filedialog
import os

class PathSelectorFrame(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        self.asset_path_var = tk.StringVar(value="(선택 안 됨)")
        self.mod_path_var = tk.StringVar(value="(선택 안 됨)")

        tk.Button(self, text="에셋 폴더 선택", command=self.select_asset).pack(side="left", padx=5)
        tk.Label(self, textvariable=self.asset_path_var, width=60, anchor="w").pack(side="left")

        tk.Button(self, text="모드 폴더 선택", command=self.select_mod).pack(side="left", padx=5)
        tk.Label(self, textvariable=self.mod_path_var, width=60, anchor="w").pack(side="left")

    def select_asset(self):
        folder = filedialog.askdirectory(title="에셋 폴더 선택", initialdir=os.getcwd())
        if folder:
            self.asset_path_var.set(folder)
            self.controller.on_asset_folder_selected(folder)

    def select_mod(self):
        folder = filedialog.askdirectory(title="모드 폴더 선택", initialdir=os.getcwd())
        if folder:
            self.mod_path_var.set(folder)
            self.controller.on_mod_folder_selected(folder)