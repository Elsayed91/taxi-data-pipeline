{% macro test_equality(model) %}

{% set compare_model = kwargs.get('compare_model') %}


{%- if target.name == 'test' -%}

select count(*) from ((select * from {{ 'test_' ~ model }} except select * from {{ compare_model }} )  union (select * from {{ compare_model }} except select * from {{ 'test_' ~ model }} )) tmp

{%- else -%}

select 0

{%- endif -%}

{% endmacro %}