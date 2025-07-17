import os
from shutil import copytree, rmtree, move
from duplicate_ini_parser import parse_ini_with_duplicates, save_ini_with_duplicates
import collections

def collect_component_file_paths(component_entries):
    result = {}
    for comp_index, component in enumerate(component_entries):
        comp_name = component["name"]
        result[comp_name] = {}

        # shared 영역
        result[comp_name]["shared"] = {}
        for key in ["ib", "blend", "position", "texcoord"]:
            if key in component["shared"]:
                val = component["shared"][key].get().strip()
                if val:
                    result[comp_name]["shared"][key] = val

        # variants 영역
        for variant_key, slots in component["variants"].items():
            result[comp_name][variant_key] = {
                key: slots[key].get().strip()
                for key in ["ib", "blend", "position", "texcoord"]
                if key in slots and slots[key].get().strip()
            }

    return result

def find_file_recursively(base_dir, filename):
    for root, _, files in os.walk(base_dir):
        if filename in files:
            return os.path.join(root, filename)
    return None

def rename_sections_and_files(ini_path, asset_name, filename_to_info, mod_folder_path):
    def format_kind_name(kind):
        return "IB" if kind.lower() == "ib" else kind.capitalize()

    config = parse_ini_with_duplicates(ini_path)
    new_config = collections.OrderedDict()
    section_rename_map = {}

    for base, (comp_name, variant_key, kind) in filename_to_info.items():
        target_section = None
        for section in config:
            if section.startswith("Resource"):
                filename = config[section].get("filename", "")
                if isinstance(filename, list):
                    filename = filename[0]
                if os.path.basename(filename) == base:
                    target_section = section
                    break

        if target_section:
            kind_str = format_kind_name(kind)
            new_section = f"Resource{asset_name}{comp_name}{variant_key}{kind_str}"
            section_rename_map[target_section] = new_section

            ext = os.path.splitext(base)[1]
            new_filename = (
                f"{asset_name}{comp_name}{variant_key}{ext}"
                if kind_str == "IB"
                else f"{asset_name}{comp_name}{kind_str}{ext}"
            )

            old_file_path = find_file_recursively(mod_folder_path, base)
            if old_file_path is None:
                continue

            rel_path = os.path.relpath(old_file_path, mod_folder_path)
            new_file_path = os.path.join(mod_folder_path, os.path.dirname(rel_path), new_filename)
            os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
            move(old_file_path, new_file_path)

            new_section_data = collections.OrderedDict(config[target_section])
            relative_path_in_ini = os.path.relpath(new_file_path, os.path.dirname(ini_path))
            new_section_data["filename"] = relative_path_in_ini.replace("\\", "/")
            new_config[new_section] = new_section_data

    for section in config:
        if section not in section_rename_map:
            new_config[section] = config[section]

    for section, kv in new_config.items():
        for key, value in kv.items():
            if isinstance(value, list):
                new_config[section][key] = [section_rename_map.get(v, v) for v in value]
            elif isinstance(value, str):
                new_config[section][key] = section_rename_map.get(value, value)

    return new_config


def export_modified_mod(mod_folder_path, output_root_path):
    mod_name = os.path.basename(mod_folder_path.rstrip("/\\"))
    output_path = os.path.join(output_root_path, mod_name)

    if os.path.exists(output_path):
        rmtree(output_path)
    copytree(mod_folder_path, output_path)
    return output_path


def generate_ini(asset_folder_path, mod_folder_path, component_slot_panel):
    component_entries = component_slot_panel.get_component_values()
    asset_name = os.path.basename(os.path.normpath(asset_folder_path))

    filename_to_info = {}
    for comp in component_entries:
        comp_name = comp["name"]
        for key, val in comp["shared"].items():
            v = val.get().strip()
            if v:
                base = os.path.basename(v)
                filename_to_info[base] = (comp_name, "", key)
        for variant_key, slots in comp["variants"].items():
            for key, val in slots.items():
                v = val.get().strip()
                if v:
                    base = os.path.basename(v)
                    filename_to_info[base] = (comp_name, variant_key, key)

    output_mod_path = export_modified_mod(mod_folder_path, "output")

    ini_paths = []
    for root, _, files in os.walk(output_mod_path):
        for file in files:
            if file.lower().endswith(".ini"):
                ini_paths.append(os.path.join(root, file))

    if not ini_paths:
        raise FileNotFoundError("output 폴더 내 ini 파일이 없습니다.")

    for ini_path in ini_paths:
        modified_config = rename_sections_and_files(
            ini_path, asset_name, filename_to_info, output_mod_path
        )
        save_ini_with_duplicates(ini_path, modified_config)