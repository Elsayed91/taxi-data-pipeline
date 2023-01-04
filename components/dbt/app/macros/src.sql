{% macro refv2(model_name)%}
  {% if target.name == 'test' %}
    {% if model_name.startswith('seed') %}
      {% do return(builtins.ref(model_name).include(database=false)) %}
    {% else %}
      {% do return(builtins.ref('test_' ~ model_name).include(database=false)) %}
    {% endif %}
  {% else %}
    {% do return(builtins.ref(model_name).include(database=false)) %}
  {% endif %}
{% endmacro %}


{% macro src(dataset_name, model_name, test_table=None) %}
  {% if target.name == 'test' %}
    {% do return(builtins.ref('test_' ~ test_table).include(database=false)) %}
  {% else %}
    {% do return(builtins.source(dataset_name, model_name).include(database=false))  %}
  {% endif %}
{% endmacro %}

{# 

{% macro refv2(model_name)%}
  {% if target.name == 'test' %}
    {% if model_name.startswith('seed') %}
      {{ ref(model_name) }}
    {% else %}
      {{ source('test_' ~ model_name) }}
    {% endif %}
  {% else %}
    {{ ref(model_name) }}
  {% endif %}
{% endmacro %} 


{% macro src(dataset_name, model_name) %}
  {% if target.name == 'test' %}
    {{ ref('test_'|string + this.name) }}
  {% else %}
    {{ source(dataset_name, model_name) }}
  {% endif %}
{% endmacro %}



{% set test_dataset = env_var('UNIT_TESTS_DATASET') | string() %}


{# {% macro refv2(model_name)%}
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
{% endmacro %} #}
 #}
