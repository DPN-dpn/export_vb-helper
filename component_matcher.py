import os
import tkinter as tk
from tkinter import filedialog, messagebox
from file_scanner import scan_folder
from ini_generator import generate_ini_text, save_ini

class ComponentMatcherApp:
    def __init__(self, root, ui_builder, logger):
        print("[component_matcher.py] ComponentMatcherApp 초기화")
        self.root = root
        self.ui = ui_builder
        self.logger = logger

        self.asset_files = []
        self.mod_files = []
        self.asset_path_var = None
        self.mod_path_var = None

    def select_mod_folder(self):
        folder = filedialog.askdirectory(title="모드 폴더 선택", initialdir=os.getcwd())
        if folder:
            self.mod_files = scan_folder(folder)
            self.mod_path_var.set(folder)
            
            self.logger.log(f"[모드 폴더 선택] {folder}")
            self.logger.log(f"불러온 파일: {len(self.mod_files)}개")

    def select_asset_folder(self):
        folder = filedialog.askdirectory(title="에셋 폴더 선택", initialdir=os.getcwd())
        if folder:
            self.asset_files = scan_folder(folder)
            self.asset_path_var.set(folder)
            
            self.logger.log(f"[에셋 폴더 선택] {folder}")
            self.logger.log(f"불러온 파일: {len(self.asset_files)}개")

    def select_file(self, component):
        path = filedialog.askopenfilename(title=f"{component}에 매칭할 파일 선택", initialdir=os.getcwd(),
                                          filetypes=[("지원되는 파일", "*.buf *.ib *.dds")])
        if path:
            self.ui.component_paths[component] = path
            self.ui.component_vars[component].set(os.path.basename(path))
            self.logger.log(f"[매칭] {component} → {os.path.basename(path)}")

    def save_ini_file(self):
        ini_text = generate_ini_text(self.ui.component_paths)
        if not ini_text:
            messagebox.showwarning("경고", "ini 내용이 비어 있습니다.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".ini", filetypes=[("INI 파일", "*.ini")])
        if path:
            save_ini(ini_text, path)
            messagebox.showinfo("저장 완료", f"ini 파일이 저장되었습니다:\n{path}")
            self.logger.log(f"[INI 저장 완료] {path}")