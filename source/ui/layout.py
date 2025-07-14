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
        self.path_selector.pack(pady=5)

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill="both", expand=True)

        self.slot_panel = ComponentSlotPanel(self.main_frame, self)
        self.slot_panel.pack(side="left", fill="both", expand=True)

        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(side="left", padx=5)
        tk.Button(self.control_frame, text="<", command=self.assign_selected_file).pack()

        self.file_panel = ModFileListPanel(self.main_frame, self)
        self.file_panel.pack(side="left", fill="y", padx=10)

        self.logger = LoggerFrame(root)
        self.logger.pack(fill="both")

    def set_selected_slot(self, index, key):
        self.selected_slot = (index, key)

    def set_selected_file(self, fname):
        self.selected_file = fname

    def assign_selected_file(self):
        if not self.selected_slot or not self.selected_file:
            return
        index, key = self.selected_slot
        self.slot_panel.set_slot_value(index, key, self.selected_file)

    def display_components(self, components, mod_files_by_type):
        self.slot_panel.display_components(components, mod_files_by_type)
        all_files = []
        for files in mod_files_by_type.values():
            all_files.extend(files)
        self.file_panel.set_file_list(all_files)

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