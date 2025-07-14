import tkinter as tk
from common import REQUIRED_COMPONENTS

class UIComponents:
    def __init__(self, root):
        print("[ui_components.py] UIComponents 초기화")
        self.root = root
        self.matcher = None
        self.component_vars = {}
        self.component_paths = {}

    def set_matcher(self, matcher):
        print("[ui_components.py] set_matcher 호출")
        self.matcher = matcher
        self.build_ui()

    def build_ui(self):
        print("[ui_components.py] build_ui 시작")
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10)

        self._folder_row(top_frame, "에셋 폴더 선택", self.matcher.select_asset_folder, is_asset=True)
        self._folder_row(top_frame, "모드 폴더 선택", self.matcher.select_mod_folder, is_asset=False)

        match_frame = tk.Frame(self.root)
        match_frame.pack(pady=10)

        for comp in REQUIRED_COMPONENTS:
            row = tk.Frame(match_frame)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=comp, width=12, anchor="w").pack(side=tk.LEFT)
            var = tk.StringVar(value="(선택 안 됨)")
            self.component_vars[comp] = var
            self.component_paths[comp] = None
            tk.Label(row, textvariable=var, width=40, anchor="w", relief="sunken").pack(side=tk.LEFT, padx=5)
            tk.Button(row, text="선택", command=lambda c=comp: self.matcher.select_file(c)).pack(side=tk.LEFT)

        tk.Button(self.root, text="ini 저장", command=self.matcher.save_ini_file).pack(pady=5)
        tk.Label(self.root, text="로그").pack(anchor="w", padx=10)

        log_text, v_scroll, h_scroll = self.matcher.logger.get_widget()
        log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")

        print("[ui_components.py] build_ui 완료")

    def _folder_row(self, parent, label, command, is_asset):
        row = tk.Frame(parent)
        row.pack(fill="x", pady=2)
        tk.Button(row, text=label, command=command).pack(side=tk.LEFT, padx=5)
        var = tk.StringVar(value="(선택 안 됨)")
        if is_asset:
            self.matcher.asset_path_var = var
        else:
            self.matcher.mod_path_var = var
        tk.Label(row, textvariable=var, anchor="w", width=80).pack(side=tk.LEFT)