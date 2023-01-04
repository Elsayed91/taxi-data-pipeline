{% macro extract_datetime_parts(timestamp_column) %}
    extract(day from {{ timestamp_column }}) as day_of_month,
    extract(month from {{ timestamp_column }}) as month,
    extract(year from {{ timestamp_column }}) as year,
    extract(dow from {{ timestamp_column }}) as day_of_week,
    extract(hour from {{ timestamp_column }}) as hour_of_day
{% endmacro %}
