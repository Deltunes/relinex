import os

def delFilesInDir(folder_path):
    # Collect every file in directory
    for filename in os.listdir(f"{folder_path}"):
        if filename == '.gitkeep':
            continue

        file_path = os.path.join(folder_path, filename)

        # Recurse if filepath is a directory
        if os.path.isdir(file_path) == True:
            delFilesInDir(file_path)
        
        try:
            # Remove file
            if os.path.isfile(file_path) or os.path.islink(file_path):
                print(f"Removing file: {file_path}")
                os.remove(file_path)
        except:
            print(f"Failed to delete {file_path}")
    