from dagster import asset

from ingestion import ingest_source_b

@asset
def source_b_files_in_minio() -> None:
    ingest_source_b.upload_raw_files_to_minio()

@asset(deps=[source_b_files_in_minio])
def raw_source_b_customers() -> None:
    ingest_source_b.load_customers_to_postgres()

@asset(deps=[source_b_files_in_minio])
def raw_source_b_contracts() -> None:
    ingest_source_b.load_contracts_to_postgres()