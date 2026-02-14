import tkinter as tk
from .path_selector import PathSelectorFrame
from .component_slot_panel import ComponentSlotPanel
from .mod_file_panel import ModFileListPanel
from .logger_frame import LoggerFrame
from app import ini_modifier
from config import load_config, save_config
import subprocess
import platform


class MainLayout:
    def __init__(self, root):
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
            asset_folder if asset_folder and os.path.exists(asset_folder) else os.getcwd()
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

        # Left column: asset selector (1) on top, component slots (3) beneath
        self.left_column = tk.Frame(self.columns_frame)
        self.left_column.pack(side="left", fill="both", expand=True)

        self.path_selector_asset = PathSelectorFrame(self.left_column, self, show_asset=True, show_mod=False)
        self.path_selector_asset.pack(side="top", fill="x", padx=5, pady=5)

        self.slot_panel = ComponentSlotPanel(self.left_column, self)
        self.slot_panel.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        # control_frame remains related to the left column (below slots)
        self.control_frame = tk.Frame(self.left_column)
        self.control_frame.pack(side="top", fill="x", padx=5, pady=5)

        # Right column: mod selector (2) on top, mod file list (4) beneath
        self.right_column = tk.Frame(self.columns_frame)
        self.right_column.pack(side="left", fill="both", expand=True)

        self.path_selector_mod = PathSelectorFrame(self.right_column, self, show_asset=False, show_mod=True)
        self.path_selector_mod.pack(side="top", fill="x", padx=5, pady=5)

        self.file_panel = ModFileListPanel(self.right_column, self)
        self.file_panel.pack(side="top", fill="both", expand=True, padx=10, pady=5)

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
        self.logger.log(msg)
    
    def on_asset_folder_selected(self, folder):
        if folder:
            self.last_asset_folder = folder
            save_config(
                {"last_asset_folder": folder, "last_mod_folder": self.last_mod_folder}
            )
            if self.matcher:
                self.matcher.select_asset_folder_from_path(folder)

    def on_mod_folder_selected(self, folder):
        if folder:
            self.last_mod_folder = folder
            save_config(
                {"last_asset_folder": self.last_asset_folder, "last_mod_folder": folder}
            )
            if self.matcher:
                self.matcher.select_mod_folder_from_path(folder)

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
