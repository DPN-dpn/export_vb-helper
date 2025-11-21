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


def save_ini_with_duplicates(path, ini_data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            for section, pairs in ini_data.items():
                f.write(f"[{section}]\n")
                for key, val in pairs.items():
                    if key.lower() == "drawindexed":
                        seen = set()

                        def write_drawindexed(item):
                            v = item["value"] if isinstance(item, dict) else item
                            if v in seen:
                                return
                            if isinstance(item, dict):
                                for c in item.get("comments", []):
                                    f.write(f"{c.lstrip()}\n")
                            f.write(f"{key} = {v}\n")
                            seen.add(v)

                        if isinstance(val, list):
                            for item in val:
                                write_drawindexed(item)
                        else:
                            write_drawindexed(val)
                    else:
                        if isinstance(val, list):
                            for v in val:
                                f.write(f"{key} = {v}\n")
                        else:
                            f.write(f"{key} = {val}\n")
                f.write("\n")
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        last = tb[-1]
        print(
            f"[save_ini_with_duplicates] {type(e).__name__}: {e}\n  File: {last.filename}, line {last.lineno}, in {last.name}\n  Code: {last.line}"
        )
        raise
