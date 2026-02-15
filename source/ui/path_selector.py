import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import os
from typing import Any, List, Optional
from config import save_config


class PathSelectorFrame(tk.Frame):
    """Rewritten Path selector logic.

    Behavior:
    1) When the user presses the folder button, the chosen path is shown in
       the label and the controller is notified (controller does persistence).
    2) The immediate subfolders of the chosen base are listed in the
       combobox.
    3) When the user explicitly chooses a combobox item, the controller is
       notified with the full subfolder path so panels/update logic run.
    4) The refresh button re-reads subfolders and re-populates the combobox.
    5) When the combobox values are updated, the first item is selected by
       default but that automatic selection does NOT notify the controller of
       the subfolder (only the base is notified when appropriate).
    6) The controller/matcher is responsible for clearing panels when
       hash.json is missing; this frame only notifies the controller.
    """

    def __init__(self, master: tk.Misc, controller: Any, show_asset: bool = True, show_mod: bool = True) -> None:
        super().__init__(master)
        self.controller = controller

        # Shared StringVar instances so multiple frames remain in sync
        self.asset_path_var = getattr(controller, "asset_path_var", tk.StringVar(value="(선택 안 됨)"))
        self.mod_path_var = getattr(controller, "mod_path_var", tk.StringVar(value="(선택 안 됨)"))
        controller.asset_path_var = self.asset_path_var
        controller.mod_path_var = self.mod_path_var

        # store the last base selected via dialog (preferred for refresh)
        self._asset_base: Optional[str] = None
        self._mod_base: Optional[str] = None

        # Build UI (keeps layout callers unchanged)
        if show_asset:
            self._build_asset_ui()
        if show_mod:
            self._build_mod_ui()

    # ---------- UI construction ----------
    def _build_asset_ui(self) -> None:
        asset_frame = tk.Frame(self)
        asset_frame.pack(side="left", fill="x", expand=True)

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

        self.asset_subvar = tk.StringVar()
        self.asset_combobox = ttk.Combobox(asset_frame, textvariable=self.asset_subvar, state="readonly")
        self.asset_combobox.pack(side="top", fill="x", padx=5, pady=(2, 5))
        self.asset_combobox.bind("<<ComboboxSelected>>", self.on_asset_sub_selected)

    def _build_mod_ui(self) -> None:
        mod_frame = tk.Frame(self)
        mod_frame.pack(side="left", fill="x", expand=True)

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

        self.mod_subvar = tk.StringVar()
        self.mod_combobox = ttk.Combobox(mod_frame, textvariable=self.mod_subvar, state="readonly")
        self.mod_combobox.pack(side="top", fill="x", padx=5, pady=(2, 5))
        self.mod_combobox.bind("<<ComboboxSelected>>", self.on_mod_sub_selected)

    # ---------- User actions ----------
    def select_asset(self) -> None:
        # Prefer dialog-selected base for initialdir, then controller's last_asset_folder,
        # then current asset_path_var, then cwd.
        initial = self._asset_base or getattr(self.controller, "last_asset_folder", None) or self.asset_path_var.get() or os.getcwd()
        folder = filedialog.askdirectory(title="에셋 폴더 선택", initialdir=initial)
        if not folder:
            return

        # update vars + label
        self.asset_path_var.set(folder)
        try:
            self.asset_display_var.set(folder)
        except Exception:
            pass
        # remember base chosen by user
        self._asset_base = folder

        # persist selection to config (do not trigger panel update)
        try:
            save_config({"last_asset_folder": folder, "last_mod_folder": getattr(self.controller, "last_mod_folder", os.getcwd())})
        except Exception:
            pass

        # populate subfolders (do not re-notify controller about subfolder)
        self.update_asset_options(notify_controller=False)

    def select_mod(self) -> None:
        initial = self._mod_base or getattr(self.controller, "last_mod_folder", None) or self.mod_path_var.get() or os.getcwd()
        folder = filedialog.askdirectory(title="모드 폴더 선택", initialdir=initial)
        if not folder:
            return

        self.mod_path_var.set(folder)
        try:
            self.mod_display_var.set(folder)
        except Exception:
            pass
        self._mod_base = folder

        # persist selection to config (do not trigger panel update)
        try:
            save_config({"last_asset_folder": getattr(self.controller, "last_asset_folder", os.getcwd()), "last_mod_folder": folder})
        except Exception:
            pass

        self.update_mod_options(notify_controller=False)

    # ---------- Helpers ----------
    def _list_subfolders(self, base: str) -> List[str]:
        try:
            names = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
            names.sort()
            return names
        except Exception:
            return []

    # ---------- Update / Refresh ----------
    def update_asset_options(self, notify_controller: bool = False) -> None:
        """Read subfolders of the asset base and populate the combobox.

        If `notify_controller` is True, inform the controller of the base
        folder (not of any subfolder). The controller (matcher) will then
        decide how to update panels; this keeps automatic refresh from
        selecting a concrete subfolder.
        """
        # Determine base directory for refresh using a clear precedence:
        # 1) dialog-selected base (`self._asset_base`)
        # 2) controller-provided `last_asset_folder` (loaded from config)
        # 3) current `asset_path_var` value
        candidate = self._asset_base if self._asset_base else getattr(self.controller, "last_asset_folder", None) or self.asset_path_var.get()
        base = candidate if candidate and os.path.isdir(candidate) else None

        if not base or not os.path.isdir(base):
            self.asset_combobox["values"] = []
            self.asset_combobox.set("")
            try:
                self.asset_refresh_btn.config(state="disabled")
                self.asset_combobox.config(state="disabled")
            except Exception:
                pass
            return

        subs = self._list_subfolders(base)
        self.asset_combobox["values"] = subs
        try:
            self.asset_combobox.config(state="readonly")
            self.asset_refresh_btn.config(state="normal")
        except Exception:
            pass

        if subs:
            # initialize to first item
            self.asset_combobox.current(0)
            # notify matcher with the auto-selected subfolder but do NOT persist
            try:
                first_selected = os.path.join(base, subs[0])
                if hasattr(self.controller, "notify_asset_subfolder_no_save"):
                    self.controller.notify_asset_subfolder_no_save(first_selected)
            except Exception:
                pass
            # Log refresh action concisely (Korean) including the refreshed base path
            try:
                if hasattr(self.controller, "log"):
                    self.controller.log(f"에셋 폴더 새로고침 완료: {base}")
            except Exception:
                pass
        else:
            self.asset_combobox.set("")

    def update_mod_options(self, notify_controller: bool = False) -> None:
        # Determine base directory for refresh using clear precedence:
        # 1) dialog-selected base (`self._mod_base`)
        # 2) controller-provided `last_mod_folder` (loaded from config)
        # 3) current `mod_path_var` value
        candidate = self._mod_base if self._mod_base else getattr(self.controller, "last_mod_folder", None) or self.mod_path_var.get()
        base = candidate if candidate and os.path.isdir(candidate) else None

        if not base or not os.path.isdir(base):
            self.mod_combobox["values"] = []
            self.mod_combobox.set("")
            try:
                self.mod_refresh_btn.config(state="disabled")
                self.mod_combobox.config(state="disabled")
            except Exception:
                pass
            return

        subs = self._list_subfolders(base)
        self.mod_combobox["values"] = subs
        try:
            self.mod_combobox.config(state="readonly")
            self.mod_refresh_btn.config(state="normal")
        except Exception:
            pass

        if subs:
            self.mod_combobox.current(0)
            try:
                first_selected = os.path.join(base, subs[0])
                if hasattr(self.controller, "notify_mod_subfolder_no_save"):
                    self.controller.notify_mod_subfolder_no_save(first_selected)
            except Exception:
                pass
            try:
                if hasattr(self.controller, "log"):
                    self.controller.log(f"모드 폴더 새로고침 완료: {base}")
            except Exception:
                pass
        else:
            self.mod_combobox.set("")

    # ---------- Combobox selections (user-driven) ----------
    def on_asset_sub_selected(self, ev: Optional[tk.Event] = None) -> None:
        base = self._asset_base if self._asset_base else self.asset_path_var.get()
        subname = self.asset_subvar.get()
        if not base or not subname:
            return
        selected = os.path.join(base, subname)
        # user explicitly chose a subfolder -> notify controller with full path
        if hasattr(self.controller, "on_asset_subfolder_selected"):
            try:
                self.controller.on_asset_subfolder_selected(selected)
            except Exception:
                pass

    def on_mod_sub_selected(self, ev: Optional[tk.Event] = None) -> None:
        base = self._mod_base if self._mod_base else self.mod_path_var.get()
        subname = self.mod_subvar.get()
        if not base or not subname:
            return
        selected = os.path.join(base, subname)
        if hasattr(self.controller, "on_mod_subfolder_selected"):
            try:
                self.controller.on_mod_subfolder_selected(selected)
            except Exception:
                pass
