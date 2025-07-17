import os
import configparser
from shutil import copytree, rmtree, move

def extract_fmt_keys_from_asset_folder(asset_folder_path):
    fmt_keys = set()
    for filename in os.listdir(asset_folder_path):
        if filename.endswith(".txt"):
            parts = filename.split("-")
            if parts:
                fmt_keys.add(parts[0])
    return sorted(fmt_keys)


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


def rename_sections_and_files(ini_path, asset_name, filename_to_info, mod_folder_path):
    def format_kind_name(kind):
        if kind.lower() == "ib":
            return "IB"
        return kind.capitalize()

    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(ini_path, encoding="utf-8", strict=False)

    new_config = configparser.ConfigParser()
    new_config.optionxform = str

    section_rename_map = {}

    for base, (comp_name, variant_key, kind) in filename_to_info.items():
        # 해당 filename을 가진 섹션 찾기
        target_section = None
        for section in config.sections():
            if section.startswith("Resource"):
                filename = config[section].get("filename", "")
                if os.path.basename(filename) == base:
                    target_section = section
                    break

        if target_section:
            kind_str = format_kind_name(kind)

            # 섹션 이름 구성
            new_section = f"Resource{asset_name}{comp_name}{variant_key}{kind_str}"
            section_rename_map[target_section] = new_section

            # 파일 이름 구성
            ext = os.path.splitext(base)[1]
            if kind_str == "IB":
                new_filename = f"{asset_name}{comp_name}{variant_key}{ext}"
            else:
                new_filename = f"{asset_name}{kind_str}{ext}"

            # 실제 파일명 변경
            old_file_path = os.path.join(mod_folder_path, base)
            new_file_path = os.path.join(mod_folder_path, new_filename)
            if os.path.exists(old_file_path):
                move(old_file_path, new_file_path)

            # 새 섹션 저장
            new_config[new_section] = config[target_section]
            new_config[new_section]["filename"] = new_filename

    # Resource가 아닌 나머지 섹션들도 그대로 복사
    for section in config.sections():
        if section not in section_rename_map:
            new_config[section] = config[section]

    # 참조된 섹션 이름들도 교체
    for section in new_config.sections():
        for key, value in new_config[section].items():
            if value in section_rename_map:
                new_config[section][key] = section_rename_map[value]

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

    # 1단계: asset_name 추출
    asset_name = os.path.basename(os.path.normpath(asset_folder_path))

    # 2단계: filename_to_info 구성
    filename_to_info = {}
    for comp in component_entries:
        comp_name = comp["name"]

        # shared
        for key, val in comp["shared"].items():
            v = val.get().strip()
            if v:
                base = os.path.basename(v)
                filename_to_info[base] = (comp_name, "", key)

        # variants
        for variant_key, slots in comp["variants"].items():
            for key, val in slots.items():
                v = val.get().strip()
                if v:
                    base = os.path.basename(v)
                    filename_to_info[base] = (comp_name, variant_key, key)

    # 3단계: output 폴더에 모드 복사
    output_mod_path = export_modified_mod(mod_folder_path, "output")

    # 4단계: ini 찾기
    ini_path = None
    for file in os.listdir(output_mod_path):
        if file.lower().endswith(".ini"):
            ini_path = os.path.join(output_mod_path, file)
            break
    if not ini_path:
        raise FileNotFoundError("output 폴더 내 ini 파일이 없습니다.")

    # 5단계: ini 수정
    modified_config = rename_sections_and_files(
        ini_path, asset_name, filename_to_info, output_mod_path
    )

    # 6단계: 저장
    with open(ini_path, "w", encoding="utf-8") as f:
        modified_config.write(f)