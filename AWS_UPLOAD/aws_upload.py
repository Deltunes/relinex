import logging
import boto3
from botocore.exceptions import ClientError
import os


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

def aws_upload(fileset=set(), outputPath="."):
    upload_dirs = ["IMAGE_SUCCESS", "RNX_SUCCESS/rinex","RNX_SUCCESS/azielev", "GIF_SUCCESS", "NAV_SUCCESS"]

    for dir in upload_dirs:
        for (root,dirs,files) in (os.walk(f"{outputPath}/{dir}",topdown=True)):
            for file in files:
                bucket_path = f"./{("/".join(root.split("/")[4:]))}/{file}"
                if bucket_path not in fileset:
                    print(bucket_path)
                    if upload_file(f"{root}/{file}", f"leaflink-rinex-doohickey", bucket_path) == True:
                        fileset.add(bucket_path)
    return fileset

if __name__ == "__main__":
    aws_upload()