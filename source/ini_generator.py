import os

OUTPUT_PATH = "./output/generated.ini"

def generate_ini(components):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    # TODO