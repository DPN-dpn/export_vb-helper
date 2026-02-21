import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "last_asset_folder": os.path.join(os.getcwd(),"assets"),
    "last_mod_folder": os.path.join(os.getcwd(),"mods"),
    "output_root": os.path.abspath("output")
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            user_config.setdefault(k, v)
        return user_config
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG


def save_config(data):
    # 기존 설정을 불러와 제공된 항목으로 업데이트한 뒤 저장합니다.
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = DEFAULT_CONFIG.copy()
    else:
        existing = DEFAULT_CONFIG.copy()

    # 전달된 값으로 덮어쓰기
    for k, v in data.items():
        existing[k] = v

    # output_root는 절대경로로 변환
    if "output_root" in existing and existing["output_root"]:
        existing["output_root"] = os.path.abspath(existing["output_root"])

    # 경로 키에 대해서는 구분자 정규화 (예: '/' -> '\\' on Windows)
    for k, v in list(existing.items()):
        if isinstance(v, str) and (k.endswith("_path") or k.endswith("_folder") or k == "output_root"):
            try:
                existing[k] = os.path.normpath(v)
            except Exception:
                # 정규화 실패 시 원본 유지
                existing[k] = v

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
