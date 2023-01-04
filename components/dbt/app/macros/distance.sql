{% macro distance(lon1, lat1, lon2, lat2) -%}
    ST_DISTANCE(ST_GEOGPOINT({{lon1}}, {{lat1}}), ST_GEOGPOINT({{lon2}},{{lat2}}))
{%- endmacro %}


{% macro distances_from_airports(lon1, lat1, lon2, lat2) -%}
    pickup_jfk_distance: ST_DISTANCE(ST_GEOGPOINT(-73.778889, 40.639722), ST_GEOGPOINT({{lon1}}, {{lat1}})),
    dropoff_jfk_distance: ST_DISTANCE(ST_GEOGPOINT(-73.778889, 40.639722), ST_GEOGPOINT({{lon2}},{{lat2}})),
    pickup_ewr_distance: ST_DISTANCE(ST_GEOGPOINT(-74.168611, 40.6925), ST_GEOGPOINT({{lon1}}, {{lat1}})),
    dropoff_ewr_distance: ST_DISTANCE(ST_GEOGPOINT(-74.168611, 40.6925), ST_GEOGPOINT({{lon2}},{{lat2}})),
    dropoff_lga_distance: ST_DISTANCE(ST_GEOGPOINT(-73.872611, 40.77725), ST_GEOGPOINT({{lon2}},{{lat2}}))
{%- endmacro %}
