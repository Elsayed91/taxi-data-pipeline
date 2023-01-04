{% macro test_equality(model) %}

{% set compare_model = kwargs.get('compare_model') %}


{%- if target.name == 'test' -%}
{% set model = builtins.ref('test_' ~ model_name).include(database=false) %}
select count(*) from ((select * from {{ model }} except select * from {{ compare_model }} )  union (select * from {{ compare_model }} except select * from {{ model }} )) tmp

{%- else -%}

select 0

{%- endif -%}

{% endmacro %}