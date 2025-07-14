# ini 텍스트 생성: 매칭된 component_paths 딕셔너리를 INI 형식 문자열로 변환
def generate_ini_text(component_paths):
    lines = []
    for key, path in component_paths.items():
        if path:  # 경로가 지정된 항목만 포함
            lines.append(f"{key}={path}")
    return "\n".join(lines)

# ini 텍스트를 실제 파일로 저장
def save_ini(text, save_path):
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)