import subprocess

def aws_download(bucketName, outputPath="."):
    dirs = ["RNX_SUCCESS/rinex","RNX_SUCCESS/azielev", "NAV_SUCCESS", "GIF_SUCCESS", "IMAGE_SUCCESS"]
    for dir in dirs:
        cmdstr = f"aws s3 cp s3://{bucketName}/{dir}/ {outputPath}/{dir}/ --recursive"
        subprocess.run(cmdstr, shell=True, check=True)

if __name__ == "__main__":
    aws_download()