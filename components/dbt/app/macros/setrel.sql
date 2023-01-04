{% macro ref_for_env(model_name) %}

{%- set normal_ref_relation = ref(model_name) -%}

{% if target.name == 'unit-test' %}

{%- set test_ref_relation = adapter.get_relation(
      database = normal_ref_relation.database,
      schema = 'models_uts',
      identifier = 'test_' ~ normal_ref_relation.identifier
) -%}
      
{{ return(test_ref_relation) }}

{% else %}

{{ return(normal_ref_relation) }}

{% endif %}

{% endmacro %}



{% macro src_for_env(dataset, table) %}

{%- set normal_ref_relation = source(dataset, table) -%}

{% if target.name == 'unit-test' %}

{%- set test_ref_relation = adapter.get_relation(
      database = normal_ref_relation.database,
      schema = 'models_uts',
      identifier = 'test_' ~ normal_ref_relation.identifier
) -%}
      
{{ return(test_ref_relation) }}

{% else %}

{{ return(normal_ref_relation) }}

{% endif %}

{% endmacro %}