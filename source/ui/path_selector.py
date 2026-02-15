import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import os
from typing import Any, List, Optional
from config import save_config


class PathSelectorFrame(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        controller: Any,
        show_asset: bool = True,
        show_mod: bool = True,
    ) -> None:
        super().__init__(master)
        self.controller = controller

        # 공유 변수
        self.asset_path_var = getattr(
            controller, "asset_path_var", tk.StringVar(value="(선택 안 됨)")
        )
        self.mod_path_var = getattr(
            controller, "mod_path_var", tk.StringVar(value="(선택 안 됨)")
        )
        controller.asset_path_var = self.asset_path_var
        controller.mod_path_var = self.mod_path_var

        # 버튼으로 직접 선택한 베이스 경로(우선 사용)
        self._asset_base: Optional[str] = None
        self._mod_base: Optional[str] = None

        if show_asset:
            self._build_asset_ui()
        if show_mod:
            self._build_mod_ui()

    def _build_asset_ui(self) -> None:
        # 유지 호환성: asset UI는 공통 빌더 사용
        self._build_selector("asset", "Assets")

    def _build_mod_ui(self) -> None:
        # 유지 호환성: mod UI는 공통 빌더 사용
        self._build_selector("mod", "Mods")

    def _build_selector(self, kind: str, button_label: str) -> None:
        """공통 셀렉터 빌더: `kind`는 'asset' 또는 'mod'"""
        frame = tk.Frame(self)
        frame.pack(side="left", fill="x", expand=True)

        controls = tk.Frame(frame)
        controls.pack(side="top", fill="x")
        btn_cmd = getattr(self, f"select_{kind}")
        tk.Button(controls, text=button_label, command=btn_cmd).grid(
            row=0, column=0, padx=5
        )

        display_var = tk.StringVar(value=getattr(self, f"{kind}_path_var").get())
        setattr(self, f"{kind}_display_var", display_var)
        tk.Label(controls, textvariable=display_var, anchor="w").grid(
            row=0, column=1, sticky="ew"
        )

        refresh_cmd = getattr(self, f"update_{kind}_options")
        refresh_btn = tk.Button(controls, text="⟳", command=refresh_cmd)
        refresh_btn.grid(row=0, column=2, padx=(4, 0))
        setattr(self, f"{kind}_refresh_btn", refresh_btn)
        controls.grid_columnconfigure(1, weight=1)

        subvar = tk.StringVar()
        setattr(self, f"{kind}_subvar", subvar)
        combobox = ttk.Combobox(frame, textvariable=subvar, state="readonly")
        combobox.pack(side="top", fill="x", padx=5, pady=(2, 5))
        combobox.bind("<<ComboboxSelected>>", getattr(self, f"on_{kind}_sub_selected"))
        setattr(self, f"{kind}_combobox", combobox)

    # ---------- 사용자 액션 ----------
    def select_asset(self) -> None:
        self._select_base("asset", "에셋 폴더 선택")

    def select_mod(self) -> None:
        self._select_base("mod", "모드 폴더 선택")

    def _select_base(self, kind: str, title: str) -> None:
        other = "mod" if kind == "asset" else "asset"
        base_attr = f"_{kind}_base"
        initial = (
            getattr(self, base_attr)
            or getattr(self.controller, f"last_{kind}_folder", None)
            or getattr(self, f"{kind}_path_var").get()
            or os.getcwd()
        )
        folder = filedialog.askdirectory(title=title, initialdir=initial)
        if not folder:
            return

        # 라벨 갱신 및 config 저장
        getattr(self, f"{kind}_path_var").set(folder)
        getattr(self, f"{kind}_display_var").set(folder)
        setattr(self, base_attr, folder)
        save_config(
            {
                "last_asset_folder": (
                    getattr(self.controller, "last_asset_folder", os.getcwd())
                    if other == "asset"
                    else folder
                ),
                "last_mod_folder": (
                    getattr(self.controller, "last_mod_folder", os.getcwd())
                    if other == "mod"
                    else folder
                ),
            }
        )

        # 하위목록 갱신
        getattr(self, f"update_{kind}_options")()

    # ---------- 헬퍼 ----------
    def _list_subfolders(self, base: str) -> List[str]:
        try:
            names = [
                d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))
            ]
            names.sort()
            return names
        except Exception:
            return []

    # ---------- 새로고침 / 초기화 ----------
    def update_asset_options(self) -> None:
        self._update_options("asset")

    def update_mod_options(self) -> None:
        self._update_options("mod")

    def _update_options(self, kind: str) -> None:
        candidate = (
            getattr(self, f"_{kind}_base")
            or getattr(self.controller, f"last_{kind}_folder", None)
            or getattr(self, f"{kind}_path_var").get()
        )
        base = candidate if candidate and os.path.isdir(candidate) else None
        combobox = getattr(self, f"{kind}_combobox")
        refresh_btn = getattr(self, f"{kind}_refresh_btn")

        if not base:
            combobox["values"] = []
            combobox.set("")
            refresh_btn.config(state="disabled")
            combobox.config(state="disabled")
            return

        subs = self._list_subfolders(base)
        combobox["values"] = subs
        combobox.config(state="readonly")
        refresh_btn.config(state="normal")

        if not subs:
            combobox.set("")
            return

        # 자동 초기화: 첫 항목 선택, 저장하지 않음
        combobox.current(0)
        first_selected = os.path.join(base, subs[0])
        fn = getattr(self.controller, f"on_{kind}_subfolder_selected", None)
        if callable(fn):
            fn(first_selected)
        log_fn = getattr(self.controller, "log", None)
        if callable(log_fn):
            label = "에셋" if kind == "asset" else "모드"
            log_fn(f"{label} 폴더 새로고침 완료: {base}")

    # ---------- 콤보박스 직접 선택 ----------
    def on_asset_sub_selected(self, ev: Optional[tk.Event] = None) -> None:
        self._on_sub_selected("asset")

    def on_mod_sub_selected(self, ev: Optional[tk.Event] = None) -> None:
        self._on_sub_selected("mod")

    def _on_sub_selected(self, kind: str) -> None:
        base = (
            getattr(self, f"_{kind}_base")
            or getattr(self.controller, f"last_{kind}_folder", None)
            or getattr(self, f"{kind}_path_var").get()
        )
        subname = getattr(self, f"{kind}_subvar").get()
        if not base or not subname:
            return
        selected = os.path.join(base, subname)
        # 콤보박스 직접 선택은 컨트롤러의 일반 핸들러로 통일 호출
        fn = getattr(self.controller, f"on_{kind}_subfolder_selected", None)
        if callable(fn):
            fn(selected)
