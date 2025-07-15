import os

OUTPUT_PATH = "./output/generated.ini"

def generate_ini(components):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for comp_name, comp_data in components.items():
            for classification, slots in comp_data["classifications"].items():
                block_name = f"TextureOverride_IB_{comp_name}_{classification}"
                f.write(f"[{block_name}]\n")
                hash_val = comp_data.get("hash", "")
                match_index = comp_data.get("match_first_index", "0")
                f.write(f"hash = {hash_val}\n")
                f.write(f"match_first_index = {match_index}\n")
                f.write(f"handling = skip\n")
                f.write(f"run = CommandListSkinTexture\n")

                ib = slots.get("ib")
                if ib:
                    f.write(f"ib = {ib}\n")

                texture_keys = {
                    "diffuse": "ps-t0",
                    "lightmap": "ps-t1",
                    "normalmap": "ps-t4",
                    "materialmap": "ps-t18",
                    "highlightmap": "ps-t18"  # highlightmap은 materialmap과 동일 취급
                }

                for key, ini_key in texture_keys.items():
                    value = slots.get(key)
                    if value:
                        f.write(f"{ini_key} = {value}\n")

                f.write(f"run = CommandList_IB_{comp_name}_{classification}\n\n")