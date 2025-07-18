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

        self.path_selector = PathSelectorFrame(root, self)
        self.path_selector.pack(pady=5, fill="x")

        self.vertical_pane = tk.PanedWindow(root, orient="vertical")
        self.vertical_pane.pack(fill="both", expand=True)

        self.main_frame = tk.Frame(self.vertical_pane)
        self.main_frame.pack(fill="both", expand=True)
        self.vertical_pane.add(self.main_frame, stretch="always")

        self.slot_panel = ComponentSlotPanel(self.main_frame, self)
        self.slot_panel.pack(side="left", fill="both", expand=True)

        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(side="left", padx=5, pady=5)

        self.file_panel = ModFileListPanel(self.main_frame, self)
        self.file_panel.pack(side="left", fill="y", padx=10)

        self.export_frame = tk.Frame(self.vertical_pane)
        self.export_button = tk.Button(self.export_frame, text="내보내기", command=self.export)
        self.export_button.pack(pady=5, padx=10, fill="x")
        self.vertical_pane.add(self.export_frame, stretch="never")

        self.logger = LoggerFrame(self.vertical_pane)
        self.logger.pack(fill="both", expand=True)
        self.vertical_pane.add(self.logger, minsize=30, stretch="always")
        
        self.config = load_config()
        self.last_asset_folder = self.config.get("last_asset_folder")
        self.last_mod_folder = self.config.get("last_mod_folder")
        
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

    def ask_folder(self, title, initial_dir=None):
        from tkinter import filedialog
        import os
        return filedialog.askdirectory(title=title, initialdir=initial_dir or os.getcwd())

    def on_asset_folder_selected(self, folder):
        if folder:
            self.last_asset_folder = folder
            save_config({
                "last_asset_folder": folder,
                "last_mod_folder": self.last_mod_folder
            })
            if self.matcher:
                self.matcher.select_asset_folder_from_path(folder)

    def on_mod_folder_selected(self, folder):
        if folder:
            self.last_mod_folder = folder
            save_config({
                "last_asset_folder": self.last_asset_folder,
                "last_mod_folder": folder
            })
            if self.matcher:
                self.matcher.select_mod_folder_from_path(folder)

    def export(self):
        try:
            asset_path = self.path_selector.asset_path_var.get()
            mod_path = self.path_selector.mod_path_var.get()
            output_root = self.config.get("output_root", "output")
            output_path = ini_modifier.generate_ini(asset_path, mod_path, self.slot_panel, output_root)
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
            self.log(f"내보내기 실패: {e}")
