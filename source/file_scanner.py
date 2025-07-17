import os

def scan_folder(folder_path):
    file_list = []
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            full_path = os.path.join(root, filename)
            file_list.append(full_path)
    return file_list
