import os
import subprocess
import platform
import tkinter as tk

from ui.path_selector import PathSelectorFrame
from ui.component_slot_panel import ComponentSlotPanel
from ui.mod_file_panel import ModFileListPanel
from ui.logger_frame import LoggerFrame

from app import ini_modifier
from config import load_config, save_config


class MainLayout:
    """Main application layout and controller for UI interactions.

    Holds references to path selector frames, panels and the matcher. This
    class is responsible for wiring user actions to the matcher and for
    persisting last-used folders via `save_config` when appropriate.
    """

    def __init__(self, root: tk.Misc) -> None:
        self.root = root
        self.matcher = None
        self.selected_slot = None
        self.selected_file = None

        import os

        # load config early so PathSelectorFrames can use initial dirs
        self.config = load_config()
        asset_folder = self.config.get("last_asset_folder")
        mod_folder = self.config.get("last_mod_folder")
        self.last_asset_folder = (
            asset_folder
            if asset_folder and os.path.exists(asset_folder)
            else os.getcwd()
        )
        self.last_mod_folder = (
            mod_folder if mod_folder and os.path.exists(mod_folder) else os.getcwd()
        )

        self.vertical_pane = tk.PanedWindow(root, orient="vertical")
        self.vertical_pane.pack(fill="both", expand=True)

        # content_frame groups top selectors and main panels; we'll arrange
        # two vertical columns so (1+3) are in the left column and (2+4) in the right.
        self.content_frame = tk.Frame(self.vertical_pane)
        self.content_frame.pack(fill="both", expand=True)

        # columns_frame holds two columns side-by-side
        self.columns_frame = tk.Frame(self.content_frame)
        self.columns_frame.pack(fill="both", expand=True)

        # Use grid for columns_frame so we can assign equal weight to both columns
        self.columns_frame.grid_rowconfigure(0, weight=1)
        # Use a uniform group so both columns get identical width allocation
        self.columns_frame.grid_columnconfigure(0, weight=1, uniform="cols")
        self.columns_frame.grid_columnconfigure(1, weight=1, uniform="cols")

        # Left column: asset selector (1) on top, component slots (3) beneath
        self.left_column = tk.Frame(self.columns_frame)
        self.left_column.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        self.path_selector_asset = PathSelectorFrame(
            self.left_column, self, show_asset=True, show_mod=False
        )
        self.path_selector_asset.pack(side="top", fill="x", padx=5, pady=5)

        self.slot_panel = ComponentSlotPanel(self.left_column, self)
        self.slot_panel.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        # control_frame remains related to the left column (below slots)
        self.control_frame = tk.Frame(self.left_column)
        self.control_frame.pack(side="top", fill="x", padx=5, pady=5)

        # Right column: mod selector (2) on top, mod file list (4) beneath
        self.right_column = tk.Frame(self.columns_frame)
        self.right_column.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        self.path_selector_mod = PathSelectorFrame(
            self.right_column, self, show_asset=False, show_mod=True
        )
        self.path_selector_mod.pack(side="top", fill="x", padx=5, pady=5)

        # Initialize path selector frames with values from config (do not re-save here)
        if hasattr(self, "path_selector_asset"):
            self.path_selector_asset.asset_path_var.set(self.last_asset_folder)
            if hasattr(self.path_selector_asset, "asset_display_var"):
                self.path_selector_asset.asset_display_var.set(self.last_asset_folder)
            self.path_selector_asset.update_asset_options()

        if hasattr(self, "path_selector_mod"):
            self.path_selector_mod.mod_path_var.set(self.last_mod_folder)
            if hasattr(self.path_selector_mod, "mod_display_var"):
                self.path_selector_mod.mod_display_var.set(self.last_mod_folder)
            self.path_selector_mod.update_mod_options()

        self.file_panel = ModFileListPanel(self.right_column, self)
        # match left-side horizontal padding to keep visual balance
        self.file_panel.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        # keep compatibility: some modules expect `ui.path_selector.asset_path_var` etc.
        self.path_selector = self

        # Remove export from content_frame and group export + logger into bottom_frame
        # Bottom frame groups export_frame and logger
        self.bottom_frame = tk.Frame(self.vertical_pane)

        # Export row (fixed height) as a child of bottom_frame
        self.export_frame = tk.Frame(self.bottom_frame, height=40)
        self.export_frame.pack_propagate(False)
        self.export_button = tk.Button(
            self.export_frame, text="내보내기", command=self.export
        )
        self.export_button.pack(pady=5, padx=10, fill="x")
        # pack export_frame at top of bottom_frame
        self.export_frame.pack(side="top", fill="x")

        # Logger fills the remainder of bottom_frame
        self.logger = LoggerFrame(self.bottom_frame)
        self.logger.pack(fill="both", expand=True)

        # Add two panes: content and bottom_frame — only the seam between them is resizable
        self.vertical_pane.add(self.content_frame, stretch="always", minsize=220)
        self.vertical_pane.add(self.bottom_frame, minsize=100, stretch="never")

    def set_matcher(self, matcher):
        self.matcher = matcher
        if not self.matcher:
            return

        # 자산/모드 기본 선택 적용 (콤보박스의 선택 우선, 없으면 마지막 경로 사용)
        self._apply_initial_selection(
            kind="asset",
            selector_attr="path_selector_asset",
            subvar_attr="asset_subvar",
            path_var_attr="asset_path_var",
            last_attr="last_asset_folder",
            matcher_method="select_asset_folder_from_path",
        )

        self._apply_initial_selection(
            kind="mod",
            selector_attr="path_selector_mod",
            subvar_attr="mod_subvar",
            path_var_attr="mod_path_var",
            last_attr="last_mod_folder",
            matcher_method="select_mod_folder_from_path",
        )

    def _apply_initial_selection(
        self,
        kind: str,
        selector_attr: str,
        subvar_attr: str,
        path_var_attr: str,
        last_attr: str,
        matcher_method: str,
    ) -> None:
        ps = getattr(self, selector_attr, None)
        selected = None
        try:
            if ps and hasattr(ps, subvar_attr):
                subname = getattr(ps, subvar_attr).get()
                base = (
                    getattr(self, path_var_attr, None)
                    and getattr(self, path_var_attr).get()
                )
                if base and subname:
                    selected = os.path.join(base, subname)
        except Exception:
            selected = None

        if selected:
            try:
                getattr(self.matcher, matcher_method)(selected)
            except Exception:
                pass
            return

        last = getattr(self, last_attr, None)
        if last:
            try:
                getattr(self.matcher, matcher_method)(last)
            except Exception:
                pass

    def set_selected_slot(self, index, key, variant=None):
        self.selected_slot = (index, key, variant)

    def set_selected_file(self, fname):
        self.selected_file = fname

    def assign_selected_file(self):
        if not self.selected_slot or not self.selected_file:
            self.log("[경고] 슬롯 또는 파일이 선택되지 않았습니다.")
            return
        try:
            index, key, variant = self.selected_slot
            self.slot_panel.set_slot_value(index, key, self.selected_file, variant)
        except Exception as e:
            self.log(f"[오류] 슬롯에 파일 할당 중 오류 발생: {e}")

    def display_components(self, components, mod_files):
        self.slot_panel.display_components(components, mod_files)
        self.file_panel.set_file_list(mod_files)

    def log(self, msg):
        # 초기화 중에는 `self.logger`가 아직 없을 수 있으니 안전하게 처리
        try:
            self.logger.log(msg)
        except Exception:
            # 로거가 없거나 오류가 발생하면 콘솔에 출력
            try:
                print(msg)
            except Exception:
                pass

    def on_asset_folder_selected(self, folder):
        if folder:
            self.last_asset_folder = folder
            save_config(
                {"last_asset_folder": folder, "last_mod_folder": self.last_mod_folder}
            )
            if self.matcher:
                self.matcher.select_asset_folder_from_path(folder)

    def on_asset_subfolder_selected(self, subfolder):
        # Called when a subfolder inside the selected Assets base is chosen
        # When a subfolder is chosen, save the base Assets folder and notify matcher
        if subfolder:
            # 콤보박스 선택은 config에 영향을 주지 않음 — matcher에만 알림
            if self.matcher:
                self.matcher.select_asset_folder_from_path(subfolder)

    def on_mod_folder_selected(self, folder):
        if folder:
            self.last_mod_folder = folder
            save_config(
                {"last_asset_folder": self.last_asset_folder, "last_mod_folder": folder}
            )
            if self.matcher:
                self.matcher.select_mod_folder_from_path(folder)

    def on_mod_subfolder_selected(self, subfolder):
        # Called when a subfolder inside the selected Mods base is chosen
        # When a subfolder is chosen, save the base Mods folder and notify matcher
        if subfolder:
            # 콤보박스 선택은 config에 영향을 주지 않음 — matcher에만 알림
            if self.matcher:
                self.matcher.select_mod_folder_from_path(subfolder)

    def export(self):
        import traceback

        try:
            # Path variables are attached to this controller by PathSelectorFrame
            asset_path = self.asset_path_var.get()
            mod_path = self.mod_path_var.get()
            output_root = self.config.get("output_root", "output")
            output_path = ini_modifier.generate_ini(
                asset_path, mod_path, self.slot_panel, output_root, self.logger
            )
            self.log("내보내기 완료")
            if self.config.get("open_after_export", True):
                import subprocess, platform

                if platform.system() == "Windows":
                    subprocess.Popen(f'explorer "{output_path}"')
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", output_path])
                else:
                    subprocess.Popen(["xdg-open", output_path])
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            last = tb[-1]
            self.log(
                f"내보내기 실패: {e}\n  File: {last.filename}, line {last.lineno}, in {last.name}\n  Code: {last.line}"
            )
