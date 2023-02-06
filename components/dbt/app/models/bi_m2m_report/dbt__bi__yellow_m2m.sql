
{{ config(
        materialized = 'view',
        dataset = env_var('HISTORICAL_DATASET'),
        tags="view" 
) }}

SELECT
  CASE
    WHEN bt.vendorid = 1 THEN 'Creative Mobile Technologies, LLC'
    WHEN bt.vendorid = 2 THEN 'VeriFone Inc.'
    ELSE 'Other'
  END AS vendors,
  EXTRACT(YEAR FROM bt.first_day_of_month) AS year,
  EXTRACT(MONTH FROM bt.first_day_of_month) AS month,
  bt.monthly_fare_amount,
  bt.average_passenger_count,
  bt.average_trip_distance,
  bt.monthly_extra_amount,
  bt.monthly_mta_tax,
  bt.monthly_tip_amount,
  bt.monthly_tolls_amount,
  bt.monthly_improvement_surcharge,
  bt.monthly_total_amount,
  bt.monthly_congestion_surcharge,
  z1.borough as pickup_borough,
  z1.zone as pickup_zone,
  z2.borough as dropoff_borough,
  z2.zone as dropoff_zone,
  IFNULL(bt.monthly_airport_fee, 0) AS airport_trip, -- 1 = yes, 0 = no
  bt.monthly_airport_fee + bt.monthly_tolls_amount + bt.monthly_congestion_surcharge +
    bt.monthly_improvement_surcharge + bt.monthly_mta_tax + bt.monthly_extra_amount AS total_extras,
  {{ payment_form(payment_type) }} AS payment_type
FROM {{ source("historical_data", "yellow_historical") }} bt
left join {{ ref("seed_zones") }} z1 on bt.pickup_zone = z1.LocationID
left join {{ ref("seed_zones") }} z2 on bt.dropoff_zone = z2.LocationID 
WHERE z1.LocationID IS NOT NULL AND z2.LocationID IS NOT NULL
AND COALESCE(average_passenger_count, 1) <= 7
AND EXTRACT(YEAR FROM bt.first_day_of_month) >= 2010 
AND EXTRACT(YEAR FROM bt.first_day_of_month) <= EXTRACT(YEAR FROM CURRENT_DATE())






