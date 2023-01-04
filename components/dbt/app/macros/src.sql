{% set test_dataset = env_var('UNIT_TESTS_DATASET') | string() %}


{% macro refv2(model_name)%}
  {% if target.name == 'test' %}
    {% if model_name.startswith('seed') %}
      {{ ref(model_name) }}
    {% else %}
      {% set rel = builtins.ref('test_' ~ model_name) %}
      {% set newrel = rel.replace_path(database=None) %}  
      {% do return(newrel) %}
    {% endif %}
  {% else %}
    {{ ref(model_name) }}
  {% endif %}
{% endmacro %} 


{% macro src(dataset_name, model_name, test_model) %}
  {% if target.name == 'test' %}
    {% set rel = builtins.ref(test_model) %}
    {% set newrel = rel.replace_path(database=None) %}  
    {% do return(newrel) %}
  {% else %}
    {{ source(dataset_name, model_name) }}
  {% endif %}
{% endmacro %}



{# 
{% macro ref_for_test(model_name) %}
 
      {%- set normal_ref_relation = ref(model_name) -%}
      {%- set test_ref_relation = this -%}

      {% if target.name == 'test' %}

            {%- set test_ref = adapter.get_relation(
                  database = test_ref_relation.database,
                  schema = test_dataset,
                  identifier = 'test_' ~ test_ref_relation.identifier) 
            -%}
            
            {{ return(test_ref) }}

      {% else %}
      
            {{ return(normal_ref_relation) }}
      
      {% endif %}
 
{% endmacro %}


{% macro source_for_test(source_schema, source_name) %}

      {%- set normal_source_relation = source(source_schema, source_name) -%}
      {%- set test_ref_relation = this -%}

      {% if target.name == 'test' %}

            {%- set test_source_relation = adapter.get_relation(
                  database = test_ref_relation.database,
                  schema = test_dataset,
                  identifier = 'test_' ~ test_ref_relation.identifier) 
            -%}
            
            {{ return(test_source_relation) }}

      {% else %}

            {{ return(normal_source_relation) }}

      {% endif %}

{% endmacro %} #}