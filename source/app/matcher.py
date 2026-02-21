import os
import json
import configparser
import re
from pathlib import Path
from app.file_manager import scan_folder


class ComponentMatcherApp:
    def __init__(self, ui):
        self.ui = ui
        self.asset_files = []
        self.mod_files = []
        self.components = []

    def select_asset_folder_from_path(self, folder):
        # 경로 정규화 및 스캔
        self.asset_files = scan_folder(folder)
        display = Path(folder).as_posix()
        self.ui.path_selector.asset_path_var.set(display)
        self.ui.log(f"[에셋 폴더 선택] {display}")
        self.ui.log(f"불러온 파일: {len(self.asset_files)}개")
        self.load_components_from_hash_json(folder)

    def select_mod_folder_from_path(self, folder):
        # 경로 정규화 및 스캔
        self.mod_files = scan_folder(folder)
        display = Path(folder).as_posix()
        self.ui.path_selector.mod_path_var.set(display)
        self.ui.log(f"[모드 폴더 선택] {display}")
        self.ui.log(f"불러온 파일: {len(self.mod_files)}개")

        # 모드 파일 목록만 갱신
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
                # 컴포넌트 초기화
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
                # 컴포넌트 초기화
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

                shared = {
                    "Blend": entry.get("blend_vb"),
                    "Position": entry.get("position_vb"),
                    "Texcoord": entry.get("texcoord_vb"),
                }

                variants = {}
                for i, label in enumerate(classifications):
                    variants[label] = {"IB": entry.get("ib")}

                components.append(
                    {"name": name, "shared": shared, "variants": variants}
                )

            self.components = components
            self.ui.display_components(self.components, self.mod_files)
        except Exception as e:
            import traceback
            self.ui.log(f"[오류] 컴포넌트 로딩 실패: {e}\n{traceback.format_exc()}")
            # 오류 시 UI 초기화
            try:
                self.components = []
                self.ui.display_components(self.components, self.mod_files or [])
            except Exception:
                pass

    def load_tree_from_mod(self, mod_files):
        # INI 파일만 필터링하여 캐시
        ini_files = [f for f in mod_files if f.lower().endswith(".ini")]
        # INI 없으면 빈 결과 반환
        if not ini_files:
            if mod_files:
                self.ui.log("모드 폴더에 .ini 파일이 없습니다.")
            return []

        mod_root = str(Path(self.ui.path_selector.mod_path_var.get()))
        self.ini_contents = {}
        self.ui.log(f"모드 루트: {mod_root} — INI 파일 {len(ini_files)}개 읽기 시작")

        # INI 파일을 읽어 캐시 (실패만 로그), 완료 후 개수만 간단히 로그
        self._cache_ini_files(mod_root, ini_files)

        # 2. 리소스(.ib/.buf) 목록 생성
        self.mod_resource_files = [
            f for f in mod_files if f.lower().endswith((".ib", ".buf", ".assets"))
        ]
        self.ui.log(f"모드 리소스(.ib/.buf) 발견: {len(self.mod_resource_files)}개")

        # 3. 패턴 생성: filename/section/kv
        filename_pattern = re.compile(
            r'^\s*filename\s*=\s*(?:"(?P<dq>[^"]+)"|\'(?P<sq>[^\']+)\'|(?P<noq>\S+))',
            re.IGNORECASE | re.MULTILINE,
        )
        section_pattern = re.compile(r"^\s*\[(?P<section>[^\]]+)\]", re.MULTILINE)
        kv_pattern = re.compile(
            r'^\s*(?P<key>[^=;\s]+)\s*=\s*(?:"(?P<dq>[^\"]+)"|\'(?P<sq>[^\']+)\'|(?P<noq>\S+))',
            re.IGNORECASE | re.MULTILINE,
        )

        rows = []

        for file_rel in self.mod_resource_files:
            aggregated = set()
            checked_sections = set()
            for ini_rel, text in self.ini_contents.items():
                comps, secs = self._find_components_in_ini_for_file(
                    ini_rel,
                    text,
                    file_rel,
                    filename_pattern,
                    section_pattern,
                    kv_pattern,
                )
                for comp, hval, section_name in comps:
                    if (comp, file_rel) not in aggregated:
                        aggregated.add((comp, file_rel))
                        rows.append((comp, hval, file_rel))
                for s in secs:
                    checked_sections.add((ini_rel, s or ""))

        return rows

    def ini_filename_points_to(self, ini_rel, ini_declared_path, file_rel):
        """INI의 경로가 대상 파일을 가리키는지 비교"""
        try:
            mod_root = str(Path(self.ui.path_selector.mod_path_var.get()))
        except Exception:
            mod_root = ""

        # ini 기준으로 선언된 경로 -> 절대
        try:
            ini_abs = (
                os.path.normpath(os.path.join(mod_root, ini_rel))
                if mod_root
                else os.path.normpath(ini_rel)
            )
            ini_dir = os.path.dirname(ini_abs)
            ini_decl_abs = os.path.normpath(os.path.join(ini_dir, ini_declared_path))
        except Exception:
            return False

        # 비교 대상 파일 절대 경로
        try:
            file_abs = (
                os.path.normpath(os.path.join(mod_root, file_rel))
                if mod_root
                else os.path.normpath(file_rel)
            )
        except Exception:
            return False

        # 윈도우는 대소문자 구분하지 않으므로 os.path.normcase로 정규화
        try:
            a = os.path.normcase(os.path.abspath(ini_decl_abs))
            b = os.path.normcase(os.path.abspath(file_abs))
        except Exception:
            a = os.path.normcase(ini_decl_abs)
            b = os.path.normcase(file_abs)

        return a == b

    def _cache_ini_files(self, mod_root, ini_files):
        """INI 읽기 및 캐시"""
        self.ini_contents = {}
        for ini_rel in ini_files:
            ini_path = os.path.join(mod_root, ini_rel)
            try:
                with open(ini_path, encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                self.ui.log(f"INI 읽기 실패: {ini_rel} -> {e}")
                continue

            self.ini_contents[ini_rel] = text

        self.ui.log(f"INI 읽기 완료: {len(self.ini_contents)}개 캐시됨")

    def _get_section_at_pos(self, text, pos):
        """pos 위치의 섹션명과 범위 반환"""
        section_pattern = re.compile(r"^\s*\[(?P<section>[^\]]+)\]", re.MULTILINE)
        starts = [(m.start(), m.group("section")) for m in section_pattern.finditer(text)]
        if not starts:
            return None, 0, len(text)

        sec_idx = None
        for i, (spos, name) in enumerate(starts):
            if spos <= pos:
                sec_idx = i
            else:
                break

        if sec_idx is None:
            return None, 0, len(text)

        sec_start = starts[sec_idx][0]
        sec_name = starts[sec_idx][1]
        sec_end = len(text) if sec_idx + 1 >= len(starts) else starts[sec_idx + 1][0]
        return sec_name, sec_start, sec_end

    def _find_components_in_ini_for_file(
        self, ini_rel, text, file_rel, filename_pattern, section_pattern, kv_pattern
    ):
        """INI에서 파일에 매핑되는 컴포넌트를 검색

        반환: ([(component, hash, section)], checked_sections)
        """
        found = []
        checked_sections = set()

        for m in filename_pattern.finditer(text):
            declared = m.group("dq") or m.group("sq") or m.group("noq")
            try:
                if not self.ini_filename_points_to(ini_rel, declared, file_rel):
                    continue
            except Exception:
                continue

            # filename 선언이 속한 섹션
            section_name, _, _ = self._get_section_at_pos(text, m.start())
            checked_sections.add(section_name or "")

            if section_name:
                target = section_name.strip()
                # 'key = 섹션명' 형태를 전체 INI에서 검색
                for kv in kv_pattern.finditer(text):
                    key = kv.group("key")
                    value = (kv.group("dq") or kv.group("sq") or kv.group("noq") or "").strip()
                    if value != target:
                        continue

                    k = key.lower()
                    comp = None
                    if k == "ib":
                        comp = "IB"
                    elif k == "vb0":
                        comp = "Position"
                    elif k == "vb2":
                        comp = "Blend"
                    elif k == "vb1":
                        comp = "Texcoord"

                    if comp:
                        # 컴포넌트 선언이 있는 섹션에서 hash 추출
                        kv_pos = kv.start()
                        comp_section_name, comp_sec_start, comp_sec_end = self._get_section_at_pos(text, kv_pos)
                        comp_section_text = text[comp_sec_start:comp_sec_end]

                        hval = ""
                        for hkv in kv_pattern.finditer(comp_section_text):
                            hkey = hkv.group("key").lower()
                            if hkey == "hash":
                                hval = hkv.group("dq") or hkv.group("sq") or hkv.group("noq") or ""
                                break

                        found.append((comp, hval, comp_section_name))

        # 동일 컴포넌트 중복 제거
        unique = []
        seen = set()
        for comp, hval, sec in found:
            if comp not in seen:
                seen.add(comp)
                unique.append((comp, hval, sec))

        return unique, checked_sections
