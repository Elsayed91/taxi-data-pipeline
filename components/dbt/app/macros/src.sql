{% macro src(func, model_name, dataset_name=None) %}
  {% if target.name == 'test' %}
    {% if model_name.startswith('seed_') %}
      {{ ref(model_name) }}
    {% elif func == 'ref' %}
      {{ ref('test_' ~ model_name) }}
    {% else %}
      {{ ref('test_'|string + this.name) }}
    {% endif %}
  {% else %}
    {% if func == 'ref' %}
      {{ ref(model_name) }}
    {% else %}
      {{ source(model_name, dataset_name) }}
    {% endif %}
  {% endif %}
{% endmacro %}