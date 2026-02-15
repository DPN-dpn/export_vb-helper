import os
import json
from pathlib import Path
from app.file_manager import scan_folder


class ComponentMatcherApp:
    def __init__(self, ui):
        self.ui = ui
        self.asset_files = []
        self.mod_files = []
        self.components = []

    def select_asset_folder_from_path(self, folder):
        # Use original folder for scanning, but normalize for UI display/logging
        self.asset_files = scan_folder(folder)
        display = Path(folder).as_posix()
        self.ui.path_selector.asset_path_var.set(display)
        self.ui.log(f"[에셋 폴더 선택] {display}")
        self.ui.log(f"불러온 파일: {len(self.asset_files)}개")
        self.load_components_from_hash_json(folder)

    def select_mod_folder_from_path(self, folder):
        # Use original folder for scanning, but normalize for UI display/logging
        self.mod_files = scan_folder(folder)
        display = Path(folder).as_posix()
        self.ui.path_selector.mod_path_var.set(display)
        self.ui.log(f"[모드 폴더 선택] {display}")
        self.ui.log(f"불러온 파일: {len(self.mod_files)}개")

        # 모드 폴더 선택은 에셋(컴포넌트) 목록을 변경하지 않고
        # 우측의 모드 파일 목록만 갱신해야 한다.
        try:
            self.ui.file_panel.set_file_list(self.mod_files)
        except Exception:
            # 예외가 발생하면 기존 동작처럼 display_components로 폴백
            try:
                self.ui.display_components(self.components, self.mod_files)
            except Exception:
                pass

    def load_components_from_hash_json(self, folder):
        try:
            path = os.path.join(folder, "hash.json")
            if not os.path.isfile(path):
                self.ui.log("에셋 폴더에 hash.json이 없습니다.")
                # clear any previously shown components when hash.json missing
                self.components = []
                try:
                    self.ui.display_components(self.components, self.mod_files)
                except Exception:
                    pass
                return

            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                self.ui.log(f"hash.json 파싱 실패: {e}")
                # clear components on parse error
                self.components = []
                try:
                    self.ui.display_components(self.components, self.mod_files)
                except Exception:
                    pass
                return

            components = []
            for entry in data:
                name = entry.get("component_name", "Unnamed")
                classifications = entry.get("object_classifications", [])

                if not classifications:
                    classifications = [""]
                    texture_sets = [texture_sets[0] if texture_sets else []]

                shared = {
                    "Blend": entry.get("blend_vb"),
                    "Position": entry.get("position_vb"),
                    "Texcoord": entry.get("texcoord_vb"),
                }

                variants = {}
                for i, label in enumerate(classifications):
                    variant = {"IB": entry.get("ib")}

                    variants[label] = variant

                components.append(
                    {"name": name, "shared": shared, "variants": variants}
                )

            self.components = components
            self.ui.display_components(self.components, self.mod_files)
        except Exception as e:
            self.ui.log(f"[오류] 컴포넌트 로딩 실패: {e}")
            # ensure UI cleared on unexpected error
            try:
                self.components = []
                self.ui.display_components(self.components, self.mod_files)
            except Exception:
                pass
