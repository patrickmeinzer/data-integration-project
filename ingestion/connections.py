from sqlalchemy import create_engine
from sqlalchemy.Engine import Engine

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