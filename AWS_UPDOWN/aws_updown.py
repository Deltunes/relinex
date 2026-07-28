import subprocess
import logging
import boto3
from botocore.exceptions import ClientError
import os

# Upload file function copied from official AWS website
def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def aws_upload(bucketName, outputPath="."):
    upload_dirs = ["OBS_SUCCESS", "NAV_SUCCESS", "OBSNAV_SUCCESS","IMAGE_SUCCESS", "GIF_SUCCESS"]

    # Get current contents of AWS bucket
    fileset = aws_list(bucketName)


    for dir in upload_dirs:
        # Go through each directory
        for (root,dirs,files) in (os.walk(f"{outputPath}/{dir}",topdown=True)):
            # Go through file in directory
            for file in files:
                if file == ".gitkeep":
                    continue

                # Generate AWS bucket output path
                rootSplit = root.split("/")
                for i in range(len(rootSplit)):
                    if rootSplit[i] in upload_dirs:
                        awsOutputPath = "/".join(rootSplit[i:])

                # Upload file to bucket if file not already in bucket
                bucket_path = f"{awsOutputPath}/{file}"
                if bucket_path not in fileset:
                    print(bucket_path)
                    upload_file(f"{root}/{file}", f"{bucketName}", bucket_path)

# Upload all contents of all directories to AWS bucket
def aws_download(bucketName, outputPath="."):
    dirs = ["OBS_SUCCESS", "NAV_SUCCESS", "OBSNAV_SUCCESS","IMAGE_SUCCESS", "GIF_SUCCESS"]
    for dir in dirs:
        cmdstr = f"aws s3 cp s3://{bucketName}/{dir}/ {outputPath}/{dir}/ --recursive"
        subprocess.run(cmdstr, shell=True, check=True)

# Get set of files currently in AWS bucket
def aws_list(bucketName):
    client = boto3.client('s3')
    pages = client.get_paginator('list_objects_v2')
    fileset = set()
    for page in pages.paginate(Bucket=bucketName):
        for content in page.get('Contents', []):
            fileset.add(content['Key'])
    return fileset