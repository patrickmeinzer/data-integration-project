import json

import pandas as pd

from . import connections
from . import config

SOURCE_B_DIR = config.PROJECT_ROOT / "data" / "synthetic" / "source_b"
DOWNLOAD_DIR = config.PROJECT_ROOT / "data" / "minio_downloads" / "source_b"


def _download_and_read_source_b_json(filename: str, key: str) -> pd.DataFrame:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    local_path = DOWNLOAD_DIR / filename

    client = connections.get_minio_client()
    connections.download_file_from_minio(
        client=client,
        bucket_name=config.MINIO_RAW_BUCKET,
        object_key=f"source_b/{filename}",
        local_path=local_path,
    )

    with open(local_path, encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data[key])


def upload_raw_files_to_minio() -> None:
    client = connections.get_minio_client()

    filenames = ["customers.json", "contracts.json"]
    for filename in filenames:
        connections.upload_file_to_minio(
            client=client,
            bucket_name=config.MINIO_RAW_BUCKET,
            local_path=SOURCE_B_DIR / filename,
            object_key=f"source_b/{filename}",
        )


def load_customers_to_postgres() -> None:
    df = _download_and_read_source_b_json("customers.json", "customers")
    engine = connections.get_postgres_engine()
    df.to_sql("raw_source_b_customers", engine, if_exists="replace", index=False)


def load_contracts_to_postgres() -> None:
    df = _download_and_read_source_b_json("contracts.json", "contracts")
    engine = connections.get_postgres_engine()
    df.to_sql("raw_source_b_contracts", engine, if_exists="replace", index=False)


def main() -> None:
    print("Lade Rohdateien nach MinIO hoch...")
    upload_raw_files_to_minio()

    print("Lade Kundendaten nach Postgres...")
    load_customers_to_postgres()

    print("Lade Vertragsdaten nach Postgres...")
    load_contracts_to_postgres()

    print("Fertig.")


if __name__ == "__main__":
    main()