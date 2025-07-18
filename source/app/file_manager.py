import os

def scan_folder(folder_path):
    file_list = []
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, folder_path).replace("\\", "/")
            file_list.append(rel_path)
    return file_list
