import os
import collections
from shutil import copytree, rmtree, move
from util.ini_parser import parse_ini_with_duplicates, save_ini_with_duplicates

def collect_filename_mapping(components):
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
    return mapping

def find_file(base_dir, filename):
    for root, _, files in os.walk(base_dir):
        if filename in files:
            return os.path.join(root, filename)
    return None

import traceback

def rename_sections_and_files(ini_path, asset_name, filename_to_info, mod_folder_path):
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
                    if os.path.basename(filename) == base:
                        kind_str = format_kind(kind)
                        new_section = f"Resource{asset_name}{comp_name}{variant_key}{kind_str}"
                        section_map[section] = new_section

                        ext = os.path.splitext(base)[1]
                        new_name = f"{asset_name}{comp_name}{variant_key}{ext}" if kind_str == "IB" else f"{asset_name}{comp_name}{kind_str}{ext}"

                        old_path = find_file(mod_folder_path, base)
                        if not old_path:
                            continue
                        rel = os.path.relpath(old_path, mod_folder_path)
                        new_path = os.path.join(mod_folder_path, os.path.dirname(rel), new_name)
                        os.makedirs(os.path.dirname(new_path), exist_ok=True)
                        move(old_path, new_path)

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
                    kv[key] = [section_map.get(v, v) for v in value]
                elif isinstance(value, str):
                    kv[key] = section_map.get(value, value)

        return new_config
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        last = tb[-1]
        print(f"[rename_sections_and_files] {type(e).__name__}: {e}\n  File: {last.filename}, line {last.lineno}, in {last.name}\n  Code: {last.line}")
        raise

def export_modified_mod(mod_folder_path, output_root):
    name = os.path.basename(mod_folder_path.rstrip("/\\"))
    output_path = os.path.join(output_root, name)
    if os.path.exists(output_path):
        rmtree(output_path)
    copytree(mod_folder_path, output_path)
    return output_path

def generate_ini(asset_folder_path, mod_folder_path, component_slot_panel, output_root="output"):
    components = component_slot_panel.get_component_values()
    asset_name = os.path.basename(os.path.normpath(asset_folder_path))
    filename_map = collect_filename_mapping(components)

    output_mod_path = export_modified_mod(mod_folder_path, output_root)

    ini_files = []
    for root, _, files in os.walk(output_mod_path):
        for file in files:
            if file.lower().endswith(".ini"):
                ini_files.append(os.path.join(root, file))

    if not ini_files:
        raise FileNotFoundError("output 폴더 내 ini 파일이 없습니다.")

    for ini_path in ini_files:
        modified = rename_sections_and_files(ini_path, asset_name, filename_map, output_mod_path)
        save_ini_with_duplicates(ini_path, modified)
    
    return output_mod_path
