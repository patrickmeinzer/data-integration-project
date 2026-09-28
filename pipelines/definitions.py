from dagster import Definitions

from pipelines import assets_source_a

defs = Definitions(
    assets=[
        assets_source_a.source_a_files_in_minio,
        assets_source_a.raw_source_a_customers,
        assets_source_a.raw_source_a_contracts,
    ],
)