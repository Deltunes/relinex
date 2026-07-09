import os

def delFilesInDir(folder_path):
    for filename in os.listdir(f"{folder_path}"):
        if filename == '.gitkeep':
            continue

        file_path = os.path.join(folder_path, filename)

        if os.path.isdir(file_path) == True:
            delFilesInDir(file_path)
        
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                print(f"Removing file: {file_path}")
                os.remove(file_path)
        except:
            print(f"Failed to delete {file_path}")
    