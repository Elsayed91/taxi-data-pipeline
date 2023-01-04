
{{ config(
        materialized = 'incremental',
        dataset = env_var('ML_DATASET'),
        partition_expiration_days = 180,
        partition_by = {'field': 'date', 'data_type': 'date',  "granularity": "month"},
) }}

{% set src = select_table(source("staging_data", "yellow_staging"), ref('test_dbt__ml__yellow_fare')) %}

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
from {{ src }} bt
left join {{ ref("seed_zones") }} z1 on bt.pulocationid = z1.LocationID
left join {{ ref("seed_zones") }} z2 on bt.dolocationid = z2.LocationID 
WHERE z1.LocationID IS NOT NULL AND z2.LocationID IS NOT NULL

{% if is_incremental() %}
{% set incremental_date = env_var('RUN_DATE', DATE(dbt_date.today())) %}
    AND DATE(bt.tpep_pickup_datetime) >= PARSE_DATE('%Y-%m-%d', DATE("{{ incremental_date }}"))
{% endif %}




