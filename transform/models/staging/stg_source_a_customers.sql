select
    kundennr                              as customer_id,
    nachname                              as last_name,
    vorname                               as first_name,
    to_date(geburtsdatum, 'DD.MM.YYYY')   as date_of_birth,
    plz                                   as postal_code,
    ort                                   as city,
    strasse                               as street
from {{ source('raw', 'raw_source_a_customers') }}