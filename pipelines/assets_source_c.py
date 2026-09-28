from dagster import asset

from ingestion import ingest_source_c

@asset
def source_c_files_in_minio() -> None:
    ingest_source_c.upload_raw_files_to_minio()

@asset(deps=[source_c_files_in_minio])
def raw_source_c_customers() -> None:
    ingest_source_c.load_customers_to_postgres()

@asset(deps=[source_c_files_in_minio])
def raw_source_c_contracts() -> None:
    ingest_source_c.load_contracts_to_postgres()