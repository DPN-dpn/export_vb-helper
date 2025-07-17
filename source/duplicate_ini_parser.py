import collections

def parse_ini_with_duplicates(path):
    ini_data = collections.OrderedDict()
    current_section = None
    temp_section = None
    temp_pairs = collections.OrderedDict()

    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith(";") or stripped.startswith("#"):
                continue

            if stripped.startswith("[") and stripped.endswith("]"):
                # 섹션 시작 전, 이전 섹션을 저장할지 결정
                if temp_section and not (
                    temp_section.startswith("Resource") and temp_pairs.get("type") == "StructuredBuffer"
                ):
                    ini_data[temp_section] = temp_pairs

                # 새 섹션 초기화
                temp_section = stripped[1:-1].strip()
                temp_pairs = collections.OrderedDict()
                continue

            if stripped.startswith(("if ", "elif", "else if", "else", "endif")):
                continue

            if "=" in stripped and temp_section:
                key, value = map(str.strip, stripped.split("=", 1))
                if key in temp_pairs:
                    existing = temp_pairs[key]
                    if isinstance(existing, list):
                        existing.append(value)
                    else:
                        temp_pairs[key] = [existing, value]
                else:
                    temp_pairs[key] = value

    # 마지막 섹션 처리
    if temp_section and not (
        temp_section.startswith("Resource") and temp_pairs.get("type") == "StructuredBuffer"
    ):
        ini_data[temp_section] = temp_pairs

    return ini_data

def save_ini_with_duplicates(path, ini_data):
    with open(path, "w", encoding="utf-8") as f:
        for section, pairs in ini_data.items():
            f.write(f"[{section}]\n")
            for key, val in pairs.items():
                if isinstance(val, list):
                    for v in val:
                        f.write(f"{key} = {v}\n")
                else:
                    f.write(f"{key} = {val}\n")
            f.write("\n")