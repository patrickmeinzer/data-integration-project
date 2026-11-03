select
    customer_id,
    split_part(full_name, ', ', 1)   as last_name,
    split_part(full_name, ', ', 2)   as first_name,
    date_of_birth::date              as date_of_birth,
    postal_code,
    city,
    email
from {{ source('raw', 'raw_source_b_customers') }}