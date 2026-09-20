from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from pathlib import Path
from typing import Union
import boto3

import config

def get_postgres_engine() -> Engine:
    connection_string = config.get_postgres_connection_string()
    return create_engine(connection_string)

def get_minio_client():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{config.MINIO_ENDPOINT}",
        aws_access_key_id=config.MINIO_ROOT_USER,
        aws_secret_access_key=config.MINIO_ROOT_PASSWORD,
    )

def ensure_bucket_exists(client, bucket_name: str) -> None:
    existing_buckets = [b["Name"] for b in client.list_buckets()["Buckets"]]
    if bucket_name not in existing_buckets:
        client.create_bucket(Bucket = bucket_name)

def upload_file_to_minio(
    client, bucket_name: str, local_path: Union[str, Path], object_key: str) -> None:
    ensure_bucket_exists(client, bucket_name)
    client.upload_file(str(local_path), bucket_name, object_key)