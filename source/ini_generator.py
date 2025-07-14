# component_vars: UI에서 가져온 StringVar 딕셔너리들
def generate_ini_text(component_vars):
    lines = []
    for comp in component_vars:
        for key, var in comp.items():
            value = var.get()
            if value:
                lines.append(f"{key}={value}")
    return "\n".join(lines)

def save_ini(text, save_path):
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)