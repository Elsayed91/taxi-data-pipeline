{% macro extract_datetime_parts(timestamp_column) %}
    extract(DAY from {{ timestamp_column }}) as day_of_month,
    extract(MONTH from {{ timestamp_column }}) as month,
    extract(YEAR from {{ timestamp_column }}) as year,
    extract(DAYOFWEEK from {{ timestamp_column }}) as day_of_week,
    extract(HOUR from {{ timestamp_column }}) as hour_of_day
{% endmacro %}
