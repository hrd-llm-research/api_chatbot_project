from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv
from fastapi import HTTPException, status

import os

load_dotenv()

minio_client = Minio(
    endpoint="110.74.194.125:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False # Set to True if you have configured TLS/SSL
)


def upload_file(bucket_name: str, object_name, file: str):
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)    


        """add a new file to the bucket"""
        minio_client.fput_object(bucket_name, object_name, file)
        print(f"File '{file}' uploaded successfully to bucket '{bucket_name}' as '{object_name}'")
    except S3Error as e:
        print(f"Error uploading file '{file}': {e}")
       
       
     
def download_file(bucket_name: str, file_name: str, savepath: str):
    try:
        if minio_client.bucket_exists(bucket_name):
            """Download the file"""
            minio_client.fget_object(bucket_name, file_name, savepath)
            print(f"File '{file_name}' downloaded successfully from bucket '{bucket_name}' to '{savepath}'")
        else:
            print(f"Bucket '{bucket_name}' does not exist.")
    except S3Error as e:
        print(f"Error downloading file '{file_name}': {e}")
        
        
def delete_bucket(bucket_name, filename: str)->None:
    # Delete the object
    try:
        minio_client.remove_object(bucket_name, filename)
        print(f"File '{filename}' has been deleted from bucket '{bucket_name}'.")
    except S3Error as e:
        print(f"Error occurred: {e}")
        
def delete_file_from_minIO(bucket_name, filename):
    try:
         # Check if the object exists (optional)
        minio_client.stat_object(bucket_name, filename)
        
        minio_client.remove_object(bucket_name, filename)
        print(f"File '{filename}' has been deleted from bucket '{bucket_name}'.")
    except S3Error as e:
        print(f"Error occurred: {e}")