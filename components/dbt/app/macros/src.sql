{% set test_dataset = env_var('UNIT_TESTS_DATASET') %}

{% macro refv2(model_name)%}
  {% if target.name == 'test' %}
    {% if model_name.startswith('seed') %}
      {{ ref(model_name) }}
    {% else %}
      {{ source(test_dataset, 'test_' ~ model_name) }}
    {% endif %}
  {% else %}
    {{ ref(model_name) }}
  {% endif %}
{% endmacro %} 


{% macro src(dataset_name, model_name) %}
  {% if target.name == 'test' %}
    {{ source(test_dataset, 'test_'|string + this.name) }}
  {% else %}
    {{ source(dataset_name, model_name) }}
  {% endif %}
{% endmacro %}


