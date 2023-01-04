
{{ config(
        materialized = 'incremental',
        dataset = 'models_ml',
        partition_expiration_days = 180,
        partition_by = {'field': 'date', 'data_type': 'date',  "granularity": "month"},
) }}

select
    bt.passenger_count,
    bt.trip_distance,
    bt.fare_amount,
    z1.longitude as pickup_long,
    z1.latitude as pickup_lat,
    z2.longitude as dropoff_long,
    z2.latitude as dropoff_lat,
    DATE(bt.tpep_pickup_datetime) as date,
    TIMESTAMP_DIFF(bt.tpep_dropoff_datetime, bt.tpep_pickup_datetime, MINUTE) AS trip_duration,
    {{ extract_datetime_parts("bt.tpep_pickup_datetime") }},
    {{ distance("z1.longitude", "z1.latitude", "z2.longitude", "z2.latitude") }} as geo_distance,
    {{
        distances_from_airports(
            "z1.longitude", "z1.latitude", "z2.longitude", "z2.latitude"
        )
    }},
from {{ source("staging_data", "yellow_staging") }} bt
left join {{ ref("seed_zones") }} z1 on bt.pulocationid = z1.LocationID
left join {{ ref("seed_zones") }} z2 on bt.dolocationid = z2.LocationID 

{% if is_incremental() %}
{% set incremental_date = env_var('RUN_DATE', default=datetime.now().strftime('%Y-%m-%d')) %}
WHERE
       DATE(bt.tpep_pickup_datetime) >= date_parse('%Y-%m-%d', "{{ incremental_date }}")
{% endif %}

