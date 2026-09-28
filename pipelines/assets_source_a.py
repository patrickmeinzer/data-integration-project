from dagster import asset

from ingestion import ingest_source_a

@asset
def source_a_files_in_minio() -> None:
    ingest_source_a.upload_raw_files_to_minio()

@asset(deps=[source_a_files_in_minio])
def raw_source_a_customers() -> None:
    ingest_source_a.load_customers_to_postgres()

@asset(deps=[source_a_files_in_minio])
def raw_source_a_contracts() -> None:
    ingest_source_a.load_contracts_to_postgres()