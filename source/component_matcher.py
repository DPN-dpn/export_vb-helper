import os
import json
from file_scanner import scan_folder

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

        self.ui.display_components(self.components, self.mod_files)

    def load_components_from_hash_json(self, folder):
        try:
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
                name = entry.get("component_name", "Unnamed")
                classifications = entry.get("object_classifications", [])
                texture_sets = entry.get("texture_hashes", [])

                if not classifications:
                    classifications = [""]
                    texture_sets = [texture_sets[0] if texture_sets else []]

                shared = {
                    "position": entry.get("position_vb"),
                    "texcoord": entry.get("texcoord_vb"),
                    "blend": entry.get("blend_vb"),
                }

                variants = {}
                for i, label in enumerate(classifications):
                    variant = {
                        "ib": entry.get("ib")
                    }

                    textures = texture_sets[i] if i < len(texture_sets) else []
                    for tex_type, _, tex_hash in textures:
                        key = tex_type.lower()
                        if key == "highlightmap":
                            variant["materialmap"] = tex_hash
                        else:
                            variant[key] = tex_hash

                    variants[label] = variant

                components.append({
                    "name": name,
                    "shared": shared,
                    "variants": variants
                })

            self.components = components
            self.ui.display_components(self.components, self.mod_files)
        except Exception as e:
            self.ui.log(f"[오류] 컴포넌트 로딩 실패: {e}")