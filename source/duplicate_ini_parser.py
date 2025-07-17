import collections

def parse_ini_with_duplicates(path):
    ini_data = collections.OrderedDict()
    current_section = None
    in_conditional = False  # if 구문 안인지 여부

    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith(";") or stripped.startswith("#"):
                continue

            if stripped.startswith("[") and stripped.endswith("]"):
                section_name = stripped[1:-1].strip()
                current_section = section_name
                ini_data[current_section] = collections.OrderedDict()
                in_conditional = False
                continue

            if stripped.startswith("if ") and "==" in stripped:
                in_conditional = True
                continue

            if stripped == "endif":
                in_conditional = False
                continue

            if "=" in stripped and current_section:
                key, value = map(str.strip, stripped.split("=", 1))
                if key in ini_data[current_section]:
                    existing = ini_data[current_section][key]
                    if isinstance(existing, list):
                        existing.append(value)
                    else:
                        ini_data[current_section][key] = [existing, value]
                else:
                    ini_data[current_section][key] = value

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