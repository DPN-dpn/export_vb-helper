import os
from file_scanner import scan_folder
from ini_generator import generate_ini_text, save_ini
from common import REQUIRED_COMPONENT_KEYS

class ComponentMatcherApp:
    def __init__(self, root, ui_builder, logger):
        self.root = root
        self.ui = ui_builder
        self.logger = logger

        self.asset_files = []
        self.mod_files = []
        self.component_sets = []  # list of dicts
        self.asset_path_var = None
        self.mod_path_var = None

    def select_mod_folder(self):
        folder = self.ui.ask_folder("모드 폴더 선택")
        if folder:
            self.mod_files = scan_folder(folder)
            self.ui.mod_path_var.set(folder)
            self.logger.log(f"[모드 폴더 선택] {folder}")
            self.logger.log(f"불러온 파일: {len(self.mod_files)}개")
            self.logger.log("")
            self.load_component_sets(folder)

    def select_asset_folder(self):
        folder = self.ui.ask_folder("에셋 폴더 선택")
        if folder:
            self.asset_files = scan_folder(folder)
            self.ui.asset_path_var.set(folder)
            self.logger.log(f"[에셋 폴더 선택] {folder}")
            self.logger.log(f"불러온 파일: {len(self.asset_files)}개")
            self.logger.log("")

    def load_component_sets(self, folder):
        ini_path = next((os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".ini")), None)
        if not ini_path:
            self.logger.log("ini 파일을 찾을 수 없습니다.")
            return

        with open(ini_path, encoding="utf-8") as f:
            lines = f.readlines()

        sets = []
        current = {}

        for line in lines:
            line = line.strip()
            if not line or line.startswith(";"):
                continue
            if line.startswith("[TextureOverride_IB_"):
                if current:
                    sets.append(current)
                current = {k: None for k in REQUIRED_COMPONENT_KEYS}
            elif "=" in line and current:
                k, v = map(str.strip, line.split("=", 1))
                if k == "ib":
                    current["ib"] = v
                elif "Position" in v:
                    current["position"] = v
                elif "Texcoord" in v:
                    current["texcoord"] = v
                elif "Blend" in v:
                    current["blend"] = v
                elif "Diffuse" in v:
                    current["diffuse"] = v
                elif "LightMap" in v:
                    current["lightmap"] = v
                elif "NormalMap" in v:
                    current["normalmap"] = v
                elif "MaterialMap" in v:
                    current["materialmap"] = v

        if current:
            sets.append(current)

        self.component_sets = sets
        self.ui.display_component_sets(self.component_sets, self.logger)