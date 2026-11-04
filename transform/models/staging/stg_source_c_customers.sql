with source as (

    select * from {{ source('raw', 'raw_source_c_customers') }}

),

parsed as (

    select
        "Cust.No."                                      as customer_id,
        "Name"                                          as full_name,
        substring(
            "Name" from
            '(?:^| )((?:(?:von|van|de|der|zu|ter|vom) )*[^ ]+(?: (?:von|van|de|der|zu|ter|vom))*)$'
        )                                                    as last_name,
        to_date("Geb.-Dat.", 'DD.MM.YYYY')              as date_of_birth,
        split_part("Adresse", ', ', 1)                  as street,
        substring("Adresse" from ', ([0-9]{5}) ')       as postal_code,
        substring("Adresse" from ', [0-9]{5} (.*)$')    as city,
        source_file
    from source

)

select
    customer_id,
    trim(left(full_name, length(full_name) - length(last_name))) as first_name,
    last_name,
    date_of_birth,
    street,
    postal_code,
    city,
    source_file
from parsed