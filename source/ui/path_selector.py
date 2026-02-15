import tkinter as tk
from tkinter import filedialog
import os
from tkinter import ttk


class PathSelectorFrame(tk.Frame):
    def __init__(self, master, controller, show_asset=True, show_mod=True):
        super().__init__(master)
        self.controller = controller

        # Share variables so multiple instances stay in sync
        self.asset_path_var = getattr(
            controller, "asset_path_var", tk.StringVar(value="(선택 안 됨)")
        )
        self.mod_path_var = getattr(
            controller, "mod_path_var", tk.StringVar(value="(선택 안 됨)")
        )
        # attach to controller for other instances
        controller.asset_path_var = self.asset_path_var
        controller.mod_path_var = self.mod_path_var

        if show_asset:
            asset_frame = tk.Frame(self)
            asset_frame.pack(side="left", fill="x", expand=True)
            # controls row: button, path label, refresh (use grid so label expands)
            asset_controls = tk.Frame(asset_frame)
            asset_controls.pack(side="top", fill="x")
            asset_btn = tk.Button(asset_controls, text="Assets", command=self.select_asset)
            asset_btn.grid(row=0, column=0, padx=5)
            self.asset_display_var = tk.StringVar(value=self.asset_path_var.get())
            self.asset_path_label = tk.Label(asset_controls, textvariable=self.asset_display_var, anchor="w")
            self.asset_path_label.grid(row=0, column=1, sticky="ew")
            self.asset_refresh_btn = tk.Button(asset_controls, text="⟳", command=self.update_asset_options)
            self.asset_refresh_btn.grid(row=0, column=2, padx=(4, 0))
            asset_controls.grid_columnconfigure(1, weight=1)

            # combobox for subfolders inside the selected Assets folder (placed under the controls row)
            self.asset_subvar = tk.StringVar()
            self.asset_combobox = ttk.Combobox(asset_frame, textvariable=self.asset_subvar, state="readonly")
            self.asset_combobox.pack(side="top", fill="x", padx=5, pady=(2, 5))
            self.asset_combobox.bind("<<ComboboxSelected>>", self.on_asset_sub_selected)

            # NOTE: do not auto-update the label from other controls; label is
            # updated only when user chooses a folder via dialog (see select_asset).

        if show_mod:
            mod_frame = tk.Frame(self)
            mod_frame.pack(side="left", fill="x", expand=True)
            # controls row: button, path label, refresh (use grid so label expands)
            mod_controls = tk.Frame(mod_frame)
            mod_controls.pack(side="top", fill="x")
            mod_btn = tk.Button(mod_controls, text="Mods", command=self.select_mod)
            mod_btn.grid(row=0, column=0, padx=5)
            self.mod_display_var = tk.StringVar(value=self.mod_path_var.get())
            self.mod_path_label = tk.Label(mod_controls, textvariable=self.mod_display_var, anchor="w")
            self.mod_path_label.grid(row=0, column=1, sticky="ew")
            self.mod_refresh_btn = tk.Button(mod_controls, text="⟳", command=self.update_mod_options)
            self.mod_refresh_btn.grid(row=0, column=2, padx=(4, 0))
            mod_controls.grid_columnconfigure(1, weight=1)

            # combobox for subfolders inside the selected Mods folder (placed under the controls row)
            self.mod_subvar = tk.StringVar()
            self.mod_combobox = ttk.Combobox(mod_frame, textvariable=self.mod_subvar, state="readonly")
            self.mod_combobox.pack(side="top", fill="x", padx=5, pady=(2, 5))
            self.mod_combobox.bind("<<ComboboxSelected>>", self.on_mod_sub_selected)

            # NOTE: do not auto-update the label from other controls; label is
            # updated only when user chooses a folder via dialog (see select_mod).

    def select_asset(self):
        folder = filedialog.askdirectory(
            title="에셋 폴더 선택", initialdir=self.controller.last_asset_folder
        )
        if folder:
            # set the base Assets folder; user will then pick a subfolder from combobox
            self.asset_path_var.set(folder)
            # set displayed label only when user chooses via dialog
            try:
                self.asset_display_var.set(folder)
            except Exception:
                pass
            self.update_asset_options()

    def select_mod(self):
        folder = filedialog.askdirectory(
            title="모드 폴더 선택", initialdir=self.controller.last_mod_folder
        )
        if folder:
            # set the base Mods folder; user will then pick a subfolder from combobox
            self.mod_path_var.set(folder)
            try:
                self.mod_display_var.set(folder)
            except Exception:
                pass
            self.update_mod_options()

    def _list_subfolders(self, base):
        try:
            entries = [
                d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))
            ]
            entries.sort()
            return entries
        except Exception:
            return []

    def update_asset_options(self):
        base = self.asset_path_var.get()
        if not base or not os.path.isdir(base):
            self.asset_combobox["values"] = []
            self.asset_combobox.set("")
            self.asset_refresh_btn.config(state="disabled")
            self.asset_combobox.config(state="disabled")
            return
        subs = self._list_subfolders(base)
        values = [os.path.join(base, s) for s in subs]
        # display only folder names in combobox
        self.asset_combobox["values"] = subs
        self.asset_combobox.config(state="readonly")
        self.asset_refresh_btn.config(state="normal")
        if subs:
            # select first by default
            self.asset_combobox.current(0)
            # notify controller about selected subfolder (do not treat as base selection)
            selected = os.path.join(base, subs[0])
            if hasattr(self.controller, "on_asset_subfolder_selected"):
                self.controller.on_asset_subfolder_selected(selected)
            else:
                self.controller.on_asset_folder_selected(selected)
        else:
            self.asset_combobox.set("")

    def on_asset_sub_selected(self, ev=None):
        base = self.asset_path_var.get()
        subname = self.asset_subvar.get()
        if base and subname:
            selected = os.path.join(base, subname)
            if hasattr(self.controller, "on_asset_subfolder_selected"):
                self.controller.on_asset_subfolder_selected(selected)
            else:
                self.controller.on_asset_folder_selected(selected)

    def update_mod_options(self):
        base = self.mod_path_var.get()
        if not base or not os.path.isdir(base):
            self.mod_combobox["values"] = []
            self.mod_combobox.set("")
            self.mod_refresh_btn.config(state="disabled")
            self.mod_combobox.config(state="disabled")
            return
        subs = self._list_subfolders(base)
        values = [os.path.join(base, s) for s in subs]
        self.mod_combobox["values"] = subs
        self.mod_combobox.config(state="readonly")
        self.mod_refresh_btn.config(state="normal")
        if subs:
            self.mod_combobox.current(0)
            selected = os.path.join(base, subs[0])
            if hasattr(self.controller, "on_mod_subfolder_selected"):
                self.controller.on_mod_subfolder_selected(selected)
            else:
                self.controller.on_mod_folder_selected(selected)
        else:
            self.mod_combobox.set("")

    def on_mod_sub_selected(self, ev=None):
        base = self.mod_path_var.get()
        subname = self.mod_subvar.get()
        if base and subname:
            selected = os.path.join(base, subname)
            if hasattr(self.controller, "on_mod_subfolder_selected"):
                self.controller.on_mod_subfolder_selected(selected)
            else:
                self.controller.on_mod_folder_selected(selected)
    
