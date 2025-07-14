import os
import json
import re
from file_scanner import scan_folder
from common import REQUIRED_COMPONENT_KEYS

def extract_name(fname):
    # 예: AstraBodyA-ib=7a110804.txt → AstraBodyA
    m = re.match(r"(.+?)-ib=", fname)
    return m.group(1) if m else None

class ComponentMatcherApp:
    def __init__(self, root, ui, logger):
        self.root = root
        self.ui = ui
        self.logger = logger

        self.asset_path_var = None
        self.mod_path_var = None

        self.asset_files = []
        self.mod_files = []
        self.components = []

    def select_asset_folder(self):
        folder = self.ui.ask_folder("에셋 폴더 선택")
        if folder:
            self.asset_files = scan_folder(folder)
            self.ui.asset_path_var.set(folder)
            self.logger.log(f"[에셋 폴더 선택] {folder}")
            self.logger.log(f"불러온 파일: {len(self.asset_files)}개")
            self.logger.log("")
            self.load_components_from_hash_json(folder)

    def select_mod_folder(self):
        folder = self.ui.ask_folder("모드 폴더 선택")
        if folder:
            self.mod_files = scan_folder(folder)
            self.ui.mod_path_var.set(folder)
            self.logger.log(f"[모드 폴더 선택] {folder}")
            self.logger.log(f"불러온 파일: {len(self.mod_files)}개")
            self.logger.log("")

            by_type = {k: [] for k in REQUIRED_COMPONENT_KEYS}
            for f in self.mod_files:
                fname = os.path.basename(f).lower()
                if fname.endswith(".buf"):
                    for key in ["ib", "position", "texcoord", "blend"]:
                        if key in fname:
                            by_type[key].append(fname)
                            break
                elif fname.endswith(".dds"):
                    for key in ["diffuse", "lightmap", "normalmap", "materialmap"]:
                        if key in fname:
                            by_type[key].append(fname)
                            break

            self.ui.display_components(self.components, self.logger, by_type)

    def load_components_from_hash_json(self, folder):
        path = os.path.join(folder, "hash.json")
        if not os.path.isfile(path):
            self.logger.log("에셋 폴더에 hash.json이 없습니다.")
            return

        with open(path, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                self.logger.log(f"hash.json 파싱 실패: {e}")
                return

        components = []

        for entry in data:
            comp = {k: None for k in REQUIRED_COMPONENT_KEYS}
            comp["name"] = entry["component_name"]
            comp["ib"] = entry.get("ib")
            comp["position"] = entry.get("position_vb")
            comp["texcoord"] = entry.get("texcoord_vb")
            comp["blend"] = entry.get("blend_vb")

            textures = entry.get("texture_hashes", [])
            if textures:
                first_set = textures[0]
                for tex_type, _, tex_hash in first_set:
                    key = tex_type.lower()
                    if key == "normalmap":
                        comp["normalmap"] = tex_hash
                    elif key == "diffuse":
                        comp["diffuse"] = tex_hash
                    elif key == "lightmap":
                        comp["lightmap"] = tex_hash
                    elif key == "materialmap":
                        comp["materialmap"] = tex_hash

            components.append(comp)

        self.components = components
        self.ui.display_components(self.components, self.logger, {})