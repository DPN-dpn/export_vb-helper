import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "last_asset_folder": None,
    "last_mod_folder": None,
    "output_root": os.path.abspath("output"),
    "open_after_export": True
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
    if "output_root" in data and data["output_root"]:
        data["output_root"] = os.path.abspath(data["output_root"])
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)