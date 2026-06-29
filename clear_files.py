import os

folder_paths = ["IMAGE_SUCCESS", "GIF_SUCCESS", "RNX_SUCCESS"]

for folder_path in folder_paths:
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")