import os
import json
from model.component import Component, Variant


def load_components_from_hash(hash_path):
    if not os.path.isfile(hash_path):
        raise FileNotFoundError("hash.json 파일이 존재하지 않습니다.")

    with open(hash_path, encoding="utf-8") as f:
        data = json.load(f)

    components = []
    for entry in data:
        name = entry.get("component_name", "Unnamed")
        shared = {k: entry.get(f"{k}_vb") for k in ["position", "texcoord", "blend"]}

        variants = {}
        for label in entry.get("object_classifications", [""]):
            variant = Variant(ib=entry.get("ib"))
            variants[label] = variant

        comp = Component(name=name, shared=shared, variants=variants)
        components.append(comp)

    return components
