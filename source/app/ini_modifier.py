import os
import collections
from shutil import copytree, rmtree, move
from util.ini_parser import parse_ini_with_duplicates, save_ini_with_duplicates

def collect_filename_mapping(components, logger=None):
    mapping = {}
    for comp in components:
        name = comp["name"]
        for key, var in comp["shared"].items():
            v = var.get().strip()
            if v:
                mapping[v] = (name, "", key)
        for variant_key, slots in comp["variants"].items():
            for key, var in slots.items():
                v = var.get().strip()
                if v:
                    mapping[v] = (name, variant_key, key)
    if logger:
        logger.log(f"[collect_filename_mapping] 매핑 결과: {mapping}")
    return mapping

def find_file(base_dir, filename):
    # 루트에 꺼내진 파일 우선 확인
    root_path = os.path.join(base_dir, os.path.basename(filename))
    if os.path.exists(root_path):
        return root_path
    # 경로가 포함된 경우 직접 확인
    direct_path = os.path.join(base_dir, filename)
    if os.path.exists(direct_path):
        return direct_path
    # 파일명만으로 전체 탐색
    fname = os.path.basename(filename)
    for root, _, files in os.walk(base_dir):
        if fname in files:
            return os.path.join(root, fname)
    return None
def extract_files_to_root(mod_folder_path, filename_map, logger=None):
    """
    매칭된 파일들과 ini 파일을 모드폴더 루트로 복사
    """
    root_dir = mod_folder_path
    extracted = set()
    # 매칭된 파일들 꺼내기
    for base in filename_map.keys():
        src_path = find_file(mod_folder_path, base)
        if src_path:
            dst_path = os.path.join(root_dir, os.path.basename(base))
            if src_path != dst_path:
                try:
                    if os.path.exists(dst_path):
                        os.remove(dst_path)
                    move(src_path, dst_path)
                    extracted.add(dst_path)
                    if logger:
                        logger.log(f"[extract_files_to_root] 파일 이동: {src_path} -> {dst_path}")
                except Exception as e:
                    if logger:
                        logger.log(f"[extract_files_to_root] 파일 이동 실패: {src_path} -> {dst_path}, {e}")
    # ini 파일 꺼내기
    for root, _, files in os.walk(mod_folder_path):
        for file in files:
            if file.lower().endswith(".ini"):
                src_path = os.path.join(root, file)
                dst_path = os.path.join(root_dir, file)
                if src_path != dst_path:
                    try:
                        if os.path.exists(dst_path):
                            os.remove(dst_path)
                        move(src_path, dst_path)
                        extracted.add(dst_path)
                        if logger:
                            logger.log(f"[extract_files_to_root] INI 이동: {src_path} -> {dst_path}")
                    except Exception as e:
                        if logger:
                            logger.log(f"[extract_files_to_root] INI 이동 실패: {src_path} -> {dst_path}, {e}")
    return list(extracted)

import traceback

def rename_sections_and_files(ini_path, asset_name, filename_to_info, mod_folder_path, logger=None):
    try:
        def format_kind(kind): return "IB" if kind.lower() == "ib" else kind.capitalize()

        config = parse_ini_with_duplicates(ini_path)
        new_config = collections.OrderedDict()
        section_map = {}

        for base, (comp_name, variant_key, kind) in filename_to_info.items():
            for section in config:
                if section.startswith("Resource"):
                    filename = config[section].get("filename", "")
                    if isinstance(filename, list): filename = filename[0]
                    if os.path.basename(filename) == os.path.basename(base):
                        kind_str = format_kind(kind)
                        new_section = f"Resource{asset_name}{comp_name}{variant_key}{kind_str}"
                        section_map[section] = new_section

                        ext = os.path.splitext(base)[1]
                        new_name = f"{asset_name}{comp_name}{variant_key}{ext}" if kind_str == "IB" else f"{asset_name}{comp_name}{kind_str}{ext}"

                        old_path = find_file(mod_folder_path, base)
                        if logger:
                            logger.log(f"[rename_sections_and_files] 섹션: {section}, 기존 파일: {filename}, 매핑키: {base}, old_path: {old_path}")
                        if not old_path:
                            if logger:
                                logger.log(f"[rename_sections_and_files] 파일을 찾을 수 없음: {base}")
                            continue
                        rel = os.path.relpath(old_path, mod_folder_path)
                        new_path = os.path.join(mod_folder_path, os.path.dirname(rel), new_name)
                        os.makedirs(os.path.dirname(new_path), exist_ok=True)
                        move(old_path, new_path)
                        if logger:
                            logger.log(f"[rename_sections_and_files] 파일 이동: {old_path} -> {new_path}")

                        new_data = collections.OrderedDict()
                        for k, v in config[section].items():
                            if k.lower() == "drawindexed":
                                new_data[k] = v
                            else:
                                # drawindexed 외에는 dict/list(dict) 구조가 오면 value만 추출
                                if isinstance(v, dict):
                                    new_data[k] = v.get("value", "")
                                elif isinstance(v, list) and v and isinstance(v[0], dict):
                                    new_data[k] = [item.get("value", "") for item in v]
                                else:
                                    new_data[k] = v
                        new_data["filename"] = os.path.relpath(new_path, os.path.dirname(ini_path)).replace("\\", "/")
                        if logger:
                            logger.log(f"[rename_sections_and_files] 섹션명 변경: {section} -> {new_section}, 파일명 변경: {filename} -> {new_data['filename']}")
                        new_config[new_section] = new_data
                        break

        for section in config:
            if section not in section_map:
                # drawindexed 외에는 dict/list(dict) 구조가 오면 value만 추출
                new_data = collections.OrderedDict()
                for k, v in config[section].items():
                    if k.lower() == "drawindexed":
                        new_data[k] = v
                    else:
                        if isinstance(v, dict):
                            new_data[k] = v.get("value", "")
                        elif isinstance(v, list) and v and isinstance(v[0], dict):
                            new_data[k] = [item.get("value", "") for item in v]
                        else:
                            new_data[k] = v
                new_config[section] = new_data

        for section, kv in new_config.items():
            for key, value in kv.items():
                if isinstance(value, list):
                    if key.lower() == "drawindexed":
                        # drawindexed는 dict 구조 허용
                        continue
                    new_list = []
                    for v in value:
                        if isinstance(v, dict):
                            val_str = v.get("value", "")
                            new_list.append(section_map.get(val_str, val_str))
                        else:
                            new_list.append(section_map.get(v, v))
                    kv[key] = new_list
                elif isinstance(value, dict):
                    if key.lower() == "drawindexed":
                        continue
                    val_str = value.get("value", "")
                    kv[key] = section_map.get(val_str, val_str)
                elif isinstance(value, str):
                    kv[key] = section_map.get(value, value)

        return new_config
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        last = tb[-1]
        if logger:
            logger.log(f"[rename_sections_and_files] {type(e).__name__}: {e}\n  File: {last.filename}, line {last.lineno}, in {last.name}\n  Code: {last.line}")
        raise

def export_modified_mod(mod_folder_path, output_root, logger=None):
    name = os.path.basename(mod_folder_path.rstrip("/\\"))
    output_path = os.path.join(output_root, name)
    if logger:
        logger.log(f"[export_modified_mod] {mod_folder_path} -> {output_path} 복사 시작")
    if os.path.exists(output_path):
        if logger:
            logger.log(f"[export_modified_mod] 기존 폴더 삭제: {output_path}")
        rmtree(output_path)
    copytree(mod_folder_path, output_path)
    if logger:
        logger.log(f"[export_modified_mod] 복사 완료: {output_path}")
    return output_path


def generate_ini(asset_folder_path, mod_folder_path, component_slot_panel, output_root="output", logger=None):
    components = component_slot_panel.get_component_values()
    asset_name = os.path.basename(os.path.normpath(asset_folder_path))
    filename_map = collect_filename_mapping(components, logger)

    output_mod_path = export_modified_mod(mod_folder_path, output_root, logger)

    # 매칭된 파일들과 ini를 루트로 꺼내기
    extract_files_to_root(output_mod_path, filename_map, logger)

    ini_files = []
    if logger:
        logger.log(f"[generate_ini] INI 파일 탐색: {output_mod_path}")
    for root, _, files in os.walk(output_mod_path):
        for file in files:
            if file.lower().endswith(".ini"):
                ini_path = os.path.join(root, file)
                # 루트에 있는 ini만 추가
                if os.path.dirname(ini_path) == output_mod_path:
                    ini_files.append(ini_path)
                    if logger:
                        logger.log(f"[generate_ini] INI 파일 발견: {ini_path}")

    if not ini_files:
        if logger:
            logger.log("[generate_ini] output 폴더 루트에 ini 파일이 없습니다.")
        raise FileNotFoundError("output 폴더 루트에 ini 파일이 없습니다.")

    for ini_path in ini_files:
        if logger:
            logger.log(f"[generate_ini] 섹션/파일명 변경 시작: {ini_path}")
        modified = rename_sections_and_files(ini_path, asset_name, filename_map, output_mod_path, logger)
        save_ini_with_duplicates(ini_path, modified)
        if logger:
            logger.log(f"[generate_ini] 섹션/파일명 변경 완료: {ini_path}")
    
    if logger:
        logger.log(f"[generate_ini] 모든 작업 완료: {output_mod_path}")
    return output_mod_path
