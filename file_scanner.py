import os

# 지정한 폴더 내의 모든 파일 경로를 재귀적으로 스캔합니다.
def scan_folder(folder_path):
    file_list = []
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            full_path = os.path.join(root, filename)
            file_list.append(full_path)
    return file_list