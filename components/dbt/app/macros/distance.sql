{% macro distance(lon1, lat1, lon2, lat2) -%}
    ST_DISTANCE(ST_GEOGPOINT({{lon1}}, {{lat1}}), ST_GEOGPOINT({{lon2}},{{lat2}}))
{%- endmacro %}


{% macro distances_from_airports(lon1, lat1, lon2, lat2) -%}
    ST_DISTANCE(ST_GEOGPOINT(-73.778889, 40.639722), ST_GEOGPOINT({{lon1}}, {{lat1}})) AS pickup_jfk_distance,
    ST_DISTANCE(ST_GEOGPOINT(-73.778889, 40.639722), ST_GEOGPOINT({{lon2}},{{lat2}})) AS dropoff_jfk_distance,
    ST_DISTANCE(ST_GEOGPOINT(-74.168611, 40.6925), ST_GEOGPOINT({{lon1}}, {{lat1}})) AS pickup_ewr_distance,
    ST_DISTANCE(ST_GEOGPOINT(-74.168611, 40.6925), ST_GEOGPOINT({{lon2}},{{lat2}})) AS dropoff_ewr_distance,
    ST_DISTANCE(ST_GEOGPOINT(-73.872611, 40.77725), ST_GEOGPOINT({{lon1}}, {{lat1}})) AS pickup_lga_distance,
    ST_DISTANCE(ST_GEOGPOINT(-73.872611, 40.77725), ST_GEOGPOINT({{lon2}},{{lat2}})) AS dropoff_lga_distance
{%- endmacro %}

