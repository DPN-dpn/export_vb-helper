import tkinter as tk
from tkinter import filedialog
import os


class PathSelectorFrame(tk.Frame):
    def __init__(self, master, controller, show_asset=True, show_mod=True):
        super().__init__(master)
        self.controller = controller

        # Share variables so multiple instances stay in sync
        self.asset_path_var = getattr(controller, "asset_path_var", tk.StringVar(value="(선택 안 됨)"))
        self.mod_path_var = getattr(controller, "mod_path_var", tk.StringVar(value="(선택 안 됨)"))
        # attach to controller for other instances
        controller.asset_path_var = self.asset_path_var
        controller.mod_path_var = self.mod_path_var

        if show_asset:
            asset_frame = tk.Frame(self)
            asset_frame.pack(side="left", fill="x", expand=True)
            tk.Button(asset_frame, text="에셋 폴더 선택", command=self.select_asset).pack(
                side="left", padx=5
            )
            tk.Label(asset_frame, textvariable=self.asset_path_var, width=60, anchor="w").pack(
                side="left", fill="x", expand=True
            )

        if show_mod:
            mod_frame = tk.Frame(self)
            mod_frame.pack(side="left", fill="x", expand=True)
            tk.Button(mod_frame, text="모드 폴더 선택", command=self.select_mod).pack(
                side="left", padx=5
            )
            tk.Label(mod_frame, textvariable=self.mod_path_var, width=60, anchor="w").pack(
                side="left", fill="x", expand=True
            )

    def select_asset(self):
        folder = filedialog.askdirectory(
            title="에셋 폴더 선택", initialdir=self.controller.last_asset_folder
        )
        if folder:
            self.asset_path_var.set(folder)
            self.controller.on_asset_folder_selected(folder)

    def select_mod(self):
        folder = filedialog.askdirectory(
            title="모드 폴더 선택", initialdir=self.controller.last_mod_folder
        )
        if folder:
            self.mod_path_var.set(folder)
            self.controller.on_mod_folder_selected(folder)
