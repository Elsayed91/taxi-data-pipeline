{{ config(materialized = 'view', dataset = 'staging') }}

WITH 
    base AS (
        SELECT
                passenger_count,
                PUlocationID,
                DOlocationID,
                trip_distance,
                fare_amount,
                data_timestamp,
                day_of_month,
                month,
                year,
                day_of_week,
                hour_of_day,
                trip_duration
        FROM
                {{ src('ref', 'base_y_ml') }}),
    zones AS (
        SELECT
                *
        FROM
                {{ src('ref', 'zones') }}),

    joined AS (
        SELECT
                base.passenger_count,
                base.PUlocationID,
                base.DOlocationID,
                base.trip_distance,
                base.fare_amount,
                base.data_timestamp,
                base.day_of_month,
                base.month,
                base.year,
                base.day_of_week,
                base.hour_of_day,
                base.trip_duration,
                z.latitude AS pickup_lat,
                z.longitude AS pickup_long,
        FROM
                base
                LEFT JOIN zones AS z
                ON base.PUlocationID = z.LocationID)

SELECT                
                joined.passenger_count,
                joined.PUlocationID,
                joined.DOlocationID,
                joined.trip_distance,
                joined.fare_amount,
                joined.data_timestamp,
                joined.day_of_month,
                joined.month,
                joined.year,
                joined.day_of_week,
                joined.hour_of_day,
                joined.trip_duration,
                joined.pickup_lat,
                joined.pickup_long,
                z.latitude AS dropoff_lat,
                z.longitude AS dropoff_long

FROM joined
LEFT JOIN zones z ON joined.DOlocationID = z.LocationID


{% set incremental_date = env_var('RUN_DATE') %}

{{ config(
        materialized = 'incremental',
        dataset = 'models_ml',
        partition_expiration_days = 180,
        partition_by = {'field': 'data_timestamp', 'data_type': 'timestamp',  "granularity": "month"},
) }}



SELECT *, {{ distance('pickup_long', 'pickup_lat', 'dropoff_long', 'dropoff_lat') }} AS distance,
        {{ distances_from_airports(pickup_long, pickup_lat, dropoff_long, dropoff_lat) }},

FROM {{ src('ref', 'int_yellow_fare') }} 


{% if is_incremental() %}
WHERE
        DATE('data_timestamp') >= date_parse('%Y-%m-%d', "{{ incremental_date }}")
{% endif %}


{{ config(materialized = 'view', dataset = 'staging') }}
SELECT passenger_count,
       PUlocationID,
       DOlocationID,
       trip_distance,
       fare_amount,
       tpep_dropoff_datetime as data_timestamp,
       {{ dbt_date.day_of_month("tpep_pickup_datetime") }} AS day_of_month,
       {{ dbt_date.date_part("month", "tpep_pickup_datetime") }} AS month,
       {{ dbt_date.date_part("year", "tpep_pickup_datetime") }} AS year,
       {{ dbt_date.date_part("dayofweek", "tpep_pickup_datetime") }} AS day_of_week,
       EXTRACT(HOUR FROM tpep_pickup_datetime at TIME zone "UTC") AS hour_of_day,
       DATE_DIFF(tpep_dropoff_datetime, tpep_pickup_datetime, MINUTE) AS trip_duration
FROM {{ src('source', 'staging_data', 'stg_yellow') }}


