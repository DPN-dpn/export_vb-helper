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
        # 스캔에는 받은 경로를 사용하되 UI 표시/로그용으로 경로 표기를 정규화함
        self.asset_files = scan_folder(folder)
        display = Path(folder).as_posix()
        self.ui.path_selector.asset_path_var.set(display)
        self.ui.log(f"[에셋 폴더 선택] {display}")
        self.ui.log(f"불러온 파일: {len(self.asset_files)}개")
        self.load_components_from_hash_json(folder)

    def select_mod_folder_from_path(self, folder):
        # 스캔에는 받은 경로를 사용하되 UI 표시/로그용으로 경로 표기를 정규화함
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
                # hash.json이 없을 때 이전에 표시하던 컴포넌트 목록을 초기화
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
                # 파싱 오류 시 컴포넌트 목록을 초기화
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
                    # 분류 정보가 없으면 빈 문자열 하나로 대체
                    classifications = [""]

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
            import traceback
            self.ui.log(f"[오류] 컴포넌트 로딩 실패: {e}\n{traceback.format_exc()}")
            # 예기치 않은 오류 발생 시 UI를 초기 상태로 복구
            try:
                self.components = []
                # mod_files가 None일 경우 대비
                self.ui.display_components(self.components, self.mod_files or [])
            except Exception:
                pass

    def load_tree_from_mod(self, mod_files):
        # 1. 모드 파일 목록에서 .ini 파일만 필터링하고 원문을 읽어 캐시합니다.
        ini_files = [f for f in mod_files if f.lower().endswith(".ini")]
        # mod_files가 비어있는 경우(예: 아직 모드 폴더가 선택되지 않음)에는
        # 불필요한 로그를 남기지 않고 빈 결과 반환
        if not ini_files:
            if mod_files:
                self.ui.log("모드 폴더에 .ini 파일이 없습니다.")
            return []

        mod_root = str(Path(self.ui.path_selector.mod_path_var.get()))
        self.ini_contents = {}
        self.ui.log(f"모드 루트: {mod_root} — INI 파일 {len(ini_files)}개 읽기 시작")

        # INI 파일을 읽어 캐시 (실패만 로그), 완료 후 개수만 간단히 로그
        self._cache_ini_files(mod_root, ini_files)

        # 2. ib/buf 파일 목록을 필터링하여 캐시
        self.mod_resource_files = [
            f for f in mod_files if f.lower().endswith((".ib", ".buf"))
        ]
        self.ui.log(f"모드 리소스(.ib/.buf) 발견: {len(self.mod_resource_files)}개")

        # 3. 각 ini 파일의 텍스트에서 filename 선언을 모두 찾아서 모드 리소스 파일과 비교
        # 패턴들 생성
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
        """
        검사 함수: ini에 적힌 파일 경로(ini 기준 상대경로)가 주어진 모드-루트 기준 파일 경로와 같은 파일을 가리키는지 확인.

        인자:
        - ini_rel: ini 파일의 모드 루트 기준 상대경로 (예: 'Folder/Sub/thing.ini')
        - ini_declared_path: ini 파일 안에 적힌 file path (ini 파일 기준 상대경로, 예: '../Meshes/x.ib')
        - file_rel: 비교 대상 파일의 모드 루트 기준 상대경로 (예: 'Folder/Meshes/x.ib')

        반환: 동일하면 True, 아니면 False
        """
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
        """INI 파일들을 읽어 `self.ini_contents`에 저장합니다. 실패와 최종 개수만 로그합니다."""
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
        """주어진 위치(pos)를 포함하는 섹션의 이름과 범위(start,end)를 반환합니다.
        섹션이 없으면 (None, 0, len(text))을 반환합니다."""
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
        """단일 INI 텍스트에서 주어진 파일(file_rel)에 매핑되는 컴포넌트를 찾습니다.

        반환값:
        - 리스트: (component, section_name) 튜플 목록
        - 집합: 확인된 섹션명들의 집합
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

            # 이 filename 선언을 포함하는 섹션을 찾음 (섹션명, 시작, 끝)
            section_name, _, _ = self._get_section_at_pos(text, m.start())
            checked_sections.add(section_name or "")

            if section_name:
                target = section_name.strip()
                # INI 전체에서 '키 = 섹션명' 형태를 검색
                for kv in kv_pattern.finditer(text):
                    key = kv.group("key")
                    value = (
                        kv.group("dq") or kv.group("sq") or kv.group("noq") or ""
                    ).strip()
                    if value != target:
                        continue

                    k = key.lower()
                    comp = None
                    if k == "ib":
                        comp = "ib"
                    elif k == "vb0":
                        comp = "position"
                    elif k == "vb2":
                        comp = "blend"
                    elif k == "vb1":
                        comp = "texcoord"

                    if comp:
                        # 컴포넌트를 선언한 구문(kv)이 존재하는 섹션을 찾음
                        kv_pos = kv.start()
                        comp_section_name, comp_sec_start, comp_sec_end = self._get_section_at_pos(text, kv_pos)
                        comp_section_text = text[comp_sec_start:comp_sec_end]

                        # 그 섹션에서 hash 키를 찾아 해시값을 얻음
                        hval = ""
                        for hkv in kv_pattern.finditer(comp_section_text):
                            hkey = hkv.group("key").lower()
                            if hkey == "hash":
                                hval = hkv.group("dq") or hkv.group("sq") or hkv.group("noq") or ""
                                break

                        # 해시는 컴포넌트를 선언한 섹션에서 가져온 값과 함께 반환
                        found.append((comp, hval, comp_section_name))

        # 컴포넌트별로 중복 제거 (같은 컴포넌트의 첫 발견만 사용)
        unique = []
        seen = set()
        for comp, hval, sec in found:
            if comp not in seen:
                seen.add(comp)
                unique.append((comp, hval, sec))

        return unique, checked_sections
