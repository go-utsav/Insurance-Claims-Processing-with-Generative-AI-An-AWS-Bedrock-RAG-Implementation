# main.py
import boto3
import os
import json
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# load the environment variables from the .env file
load_dotenv()

bucket_name = os.getenv('BUCKET_NAME')
if not bucket_name:
    raise ValueError("BUCKET_NAME must be set in .env")

s3 = boto3.client('s3', region_name=os.getenv('AWS_REGION'), aws_access_key_id=os.getenv('AWS_ACCESS_KEY'), aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))

# Create bucket if it doesn't exist (head_bucket raises 404 when bucket is missing)
try:
    s3.head_bucket(Bucket=bucket_name)
    print(f"Bucket '{bucket_name}' already exists")
except ClientError as e:
    if e.response["Error"]["Code"] == "404":
        region = os.getenv("AWS_REGION")
        if region == "us-west-2":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": region})
        print(f"Bucket '{bucket_name}' created successfully")
    else:
        raise

# list all contents of the bucket
print(s3.list_objects(Bucket=bucket_name))


# upload a file to the bucket
s3.upload_file(Filename='claim-document.pdf', Bucket=os.getenv('BUCKET_NAME'), Key='claim-document.pdf')
print(f"File uploaded to {os.getenv('BUCKET_NAME')}")

# # download a file from the bucket
# s3.download_file(Bucket=os.getenv('BUCKET_NAME'), Key='claim-document.pdf', Filename='claim-document.pdf')
# print(f"File downloaded from {os.getenv('BUCKET_NAME')}")