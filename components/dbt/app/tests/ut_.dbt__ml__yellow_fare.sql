{# {% call dbt_unit_testing.test('dbt__ml__yellow_fare', 'should calculate distance, distance_from_airports, and date parts correctly') %}
{% call dbt_unit_testing.mock_source ('staging_data', 'yellow_staging', {"input_format": "csv"}) %}
passenger_count | trip_distance | fare_amount | tpep_pickup_datetime | PULocationID | DOLocationID
1 | 2.5 | 10.5 | 2021-01-01 00:00:00 | 1 | 2
{% endcall %}

{% call dbt_unit_testing.mock_ref ('seeds_zoones', {"input_format": "csv"}) %}
location_id | longitude | latitude
1 | -73.99 | 40.75
2 | -73.99 | 40.73
{% endcall %}

{% call dbt_unit_testing.expect({"input_format": "csv"}) %}
passenger_count | trip_distance | fare_amount | day_of_month | month | year | day_of_week | hour_of_day | distance | distance_from_lga | distance_from_jfk
1 | 2.5 | 10.5 | 1 | 1 | 2021 | 2 | 0 | 1.3697 | 2.2224 | 3.4736
{% endcall %}
{% endcall %} #}