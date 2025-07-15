import tkinter as tk
from .path_selector import PathSelectorFrame
from .component_slot_panel import ComponentSlotPanel
from .mod_file_panel import ModFileListPanel
from .logger_frame import LoggerFrame

class UIComponents:
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
        tk.Button(self.control_frame, text="<", command=self.assign_selected_file).pack()

        self.file_panel = ModFileListPanel(self.main_frame, self)
        self.file_panel.pack(side="left", fill="y", padx=10)

        self.export_frame = tk.Frame(self.vertical_pane)
        self.export_button = tk.Button(self.export_frame, text="내보내기", command=self.export)
        self.export_button.pack(pady=5, padx=10, fill="x")
        self.vertical_pane.add(self.export_frame, stretch="never")

        self.logger = LoggerFrame(self.vertical_pane)
        self.logger.pack(fill="both", expand=True)
        self.vertical_pane.add(self.logger, minsize=30, stretch="always")

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

    def ask_folder(self, title):
        from tkinter import filedialog
        import os
        return filedialog.askdirectory(title=title, initialdir=os.getcwd())

    def on_asset_folder_selected(self, folder):
        if self.matcher:
            self.matcher.select_asset_folder_from_path(folder)

    def on_mod_folder_selected(self, folder):
        if self.matcher:
            self.matcher.select_mod_folder_from_path(folder)

    def export(self):
        # TODO
        pass