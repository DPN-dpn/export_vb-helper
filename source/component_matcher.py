import os
import json
from file_scanner import scan_folder
from common import REQUIRED_COMPONENT_KEYS

class ComponentMatcherApp:
    def __init__(self, root, ui):
        self.root = root
        self.ui = ui
        self.asset_files = []
        self.mod_files = []
        self.components = []

    def select_asset_folder_from_path(self, folder):
        self.asset_files = scan_folder(folder)
        self.ui.path_selector.asset_path_var.set(folder)
        self.ui.log(f"[에셋 폴더 선택] {folder}")
        self.ui.log(f"불러온 파일: {len(self.asset_files)}개")
        self.ui.log("")
        self.load_components_from_hash_json(folder)

    def select_mod_folder_from_path(self, folder):
        self.mod_files = scan_folder(folder)
        self.ui.path_selector.mod_path_var.set(folder)
        self.ui.log(f"[모드 폴더 선택] {folder}")
        self.ui.log(f"불러온 파일: {len(self.mod_files)}개")
        self.ui.log("")

        by_type = self._categorize_files_by_type(self.mod_files)
        self.ui.display_components(self.components, by_type)

    def load_components_from_hash_json(self, folder):
        path = os.path.join(folder, "hash.json")
        if not os.path.isfile(path):
            self.ui.log("에셋 폴더에 hash.json이 없습니다.")
            return

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.ui.log(f"hash.json 파싱 실패: {e}")
            return

        components = []
        for entry in data:
            comp = {k: None for k in REQUIRED_COMPONENT_KEYS}
            comp["ib"] = entry.get("ib")
            comp["position"] = entry.get("position_vb")
            comp["texcoord"] = entry.get("texcoord_vb")
            comp["blend"] = entry.get("blend_vb")

            textures = entry.get("texture_hashes", [])
            if textures:
                for tex_type, _, tex_hash in textures[0]:
                    key = tex_type.lower()
                    if key in comp:
                        comp[key] = tex_hash
                    elif key == "highlightmap":
                        comp["materialmap"] = tex_hash

            comp["name"] = entry.get("component_name", "Unnamed")
            components.append(comp)

        self.components = components
        self.ui.display_components(self.components, {})

    def _categorize_files_by_type(self, files):
        by_type = {k: [] for k in REQUIRED_COMPONENT_KEYS}
        for f in files:
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
        return by_type