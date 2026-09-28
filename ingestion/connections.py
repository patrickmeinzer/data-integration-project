from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from pathlib import Path
from typing import List, Union
import boto3

from . import config

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

def download_file_from_minio(
    client, bucket_name: str, object_key: str, local_path: Union[str, Path]) -> None:
    client.download_file(bucket_name, object_key, str(local_path))

def list_objects_in_minio(client, bucket_name: str, prefix: str) -> List[str]:
    response = client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    return [obj["Key"] for obj in response.get("Contents", [])]