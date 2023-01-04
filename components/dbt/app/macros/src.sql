{% macro src(dataset=None, model_name=None, test_model=None) %}
    {% if target.name == 'test' %}
        {% if dataset %}
            {{ ref('test_' ~ test_model) }}
        {% elif model_name %}
            {{ ref('test_' ~ model_name) }}
        {% endif %}
    {% else %}
        {% if dataset %}
            {{ source(dataset, model_name) }}
        {% elif model_name %}
            {{ ref(model_name) }}
        {% endif %}
    {% endif %}
{% endmacro %}



{# {% macro ref(model_name)%}
  {% if target.name == 'test' %}
    {% if model_name.startswith('seed') or model_name.endswith('_expected') %}
      {% do return(builtins.ref(model_name).include(database=false)) %}
    {% elif model_name.startswith('dbt__') %}
      {% do return(builtins.ref('test_' ~ model_name).include(database=false)) %}
    {% endif %}
  {% else %}
    {% do return(builtins.ref(model_name).include(database=false)) %}
  {% endif %}
{% endmacro %}


{% macro source(dataset_name, model_name, test_table=None) %}
  {% if target.name == 'test' and test_table is not none and test_table.startswith('dbt__') %}
    {% do return(builtins.ref('test_' ~ test_table).include(database=false)) %}
  {% else %}
    {% do return(builtins.source(dataset_name, model_name).include(database=false))  %}
  {% endif %}
{% endmacro %} #}

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
