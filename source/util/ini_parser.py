import collections
import traceback


def parse_ini_with_duplicates(path):
    ini_data = collections.OrderedDict()
    temp_section = None
    temp_pairs = collections.OrderedDict()
    temp_comments = []
    last_if_comment = []
    in_if_block = False

    def add_key_with_comment(key, value, comments):
        # drawindexed에만 주석 연결, 아니면 일반 저장
        if key.lower() == "drawindexed":
            temp_pairs[key] = {
                "value": value,
                "comments": list(comments) if comments else [],
            }
        else:
            temp_pairs[key] = value

    with open(path, encoding="utf-8") as f:
        for line in f:
            raw = line.rstrip("\n")
            stripped = raw.strip()
            if not stripped:
                temp_comments.clear()
                continue

            if stripped.startswith("[") and stripped.endswith("]"):
                if temp_section and not (
                    temp_section.startswith("Resource")
                    and temp_pairs.get("type") == "StructuredBuffer"
                ):
                    ini_data[temp_section] = temp_pairs
                temp_section = stripped[1:-1].strip()
                temp_pairs = collections.OrderedDict()
                temp_comments.clear()
                last_if_comment.clear()
                in_if_block = False
                continue

            if stripped.startswith(("if ", "elif", "else if", "else")):
                in_if_block = True
                if temp_comments:
                    last_if_comment = list(temp_comments)
                temp_comments.clear()
                continue
            if stripped.startswith("endif"):
                in_if_block = False
                last_if_comment.clear()
                temp_comments.clear()
                continue

            # 주석 처리된 drawindexed도 파싱
            if stripped.startswith(";") or stripped.startswith("#"):
                comment_content = stripped.lstrip(";# ")
                if (
                    comment_content.lower().startswith("drawindexed")
                    and "=" in comment_content
                ):
                    # drawindexed = ... 형태의 주석 해제
                    key, value = map(str.strip, comment_content.split("=", 1))
                    comments_to_attach = list(temp_comments) if temp_comments else []
                    if key in temp_pairs:
                        existing = temp_pairs[key]
                        if isinstance(existing, dict):
                            temp_pairs[key] = [
                                existing,
                                {"value": value, "comments": comments_to_attach},
                            ]
                        elif isinstance(existing, list):
                            temp_pairs[key].append(
                                {"value": value, "comments": comments_to_attach}
                            )
                    else:
                        temp_pairs[key] = {
                            "value": value,
                            "comments": comments_to_attach,
                        }
                    temp_comments.clear()
                else:
                    temp_comments.append(raw)
                continue

            if "=" in stripped and temp_section:
                key, value = map(str.strip, stripped.split("=", 1))
                # drawindexed에만 주석 연결
                comments_to_attach = []
                if key.lower() == "drawindexed":
                    if temp_comments:
                        comments_to_attach.extend(temp_comments)
                    if in_if_block and last_if_comment:
                        # if문 내 drawindexed면 if문 주석도 추가
                        for c in last_if_comment:
                            if c not in comments_to_attach:
                                comments_to_attach.append(c)
                if key in temp_pairs:
                    existing = temp_pairs[key]
                    if key.lower() == "drawindexed":
                        # 여러 drawindexed가 있을 때 각각 주석도 리스트로
                        if isinstance(existing, dict):
                            temp_pairs[key] = [
                                existing,
                                {"value": value, "comments": comments_to_attach},
                            ]
                        elif isinstance(existing, list):
                            temp_pairs[key].append(
                                {"value": value, "comments": comments_to_attach}
                            )
                    else:
                        if isinstance(existing, list):
                            existing.append(value)
                        else:
                            temp_pairs[key] = [existing, value]
                else:
                    if key.lower() == "drawindexed":
                        add_key_with_comment(key, value, comments_to_attach)
                    else:
                        temp_pairs[key] = value
                temp_comments.clear()

    if temp_section and not (
        temp_section.startswith("Resource")
        and temp_pairs.get("type") == "StructuredBuffer"
    ):
        ini_data[temp_section] = temp_pairs

    return ini_data


def save_ini_with_duplicates(original_path, replacements, output_path=None):
    """
    원본 ini 파일을 문자열로 읽고, replacements dict에 있는 key-value만 찾아서 value를 교체하여 저장.
    original_path: 원본 ini 파일 경로
    replacements: {section: {key: value}} 형태의 dict
    output_path: 저장할 파일 경로 (None이면 original_path에 덮어씀)
    """
    import re
    import traceback
    try:
        with open(original_path, encoding="utf-8") as f:
            ini_text = f.read()

        # 1차: 모든 교체 대상 값을 임시문자열로 치환
        temp_map = {}  # {(section, key): temp_str}
        for section, pairs in replacements.items():
            section_pattern = re.compile(rf"^\[{re.escape(section)}\]$", re.MULTILINE)
            section_match = section_pattern.search(ini_text)
            if not section_match:
                print(f"[save_ini_with_duplicates] 섹션 '{section}'을(를) 찾을 수 없습니다.")
                continue
            section_start = section_match.end()
            next_section_match = re.search(r"^\[.*\]$", ini_text[section_start:], re.MULTILINE)
            section_end = section_start + next_section_match.start() if next_section_match else len(ini_text)
            section_body = ini_text[section_start:section_end]

            for key, value in pairs.items():
                temp_str = f"[__REPLACE_KEY_{section}_{key}__]"
                temp_map[(section, key)] = (temp_str, value)
                key_pattern = re.compile(rf"(^[ \t;#]*{re.escape(key)}[ \t]*=[ \t]*)(.*)$", re.MULTILINE)
                def repl_temp(m):
                    print(f"[save_ini_with_duplicates] '{section}' 섹션의 '{key}' 값을 임시문자열로 먼저 치환.")
                    return m.group(1) + temp_str
                section_body_new = key_pattern.sub(repl_temp, section_body)
                if section_body == section_body_new:
                    print(f"[save_ini_with_duplicates] '{section}' 섹션에 '{key}' 키를 찾지 못했습니다.")
                section_body = section_body_new

            ini_text = ini_text[:section_start] + section_body + ini_text[section_end:]

        # 2차: 임시문자열을 실제 값으로 치환
        for (section, key), (temp_str, value) in temp_map.items():
            ini_text = ini_text.replace(temp_str, str(value))
            print(f"[save_ini_with_duplicates] 임시문자열 {temp_str}을(를) 실제 값 '{value}'로 치환.")

        save_path = output_path if output_path else original_path
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(ini_text)
        print(f"[save_ini_with_duplicates] 파일 저장 성공: {save_path}")
    except Exception as e:
        print(f"[save_ini_with_duplicates] 파일 저장 중 오류 발생: {e}")
        traceback.print_exc()
