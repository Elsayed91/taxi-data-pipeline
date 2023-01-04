{# {% macro src(func, model_name, dataset_name=None) %}
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
      {{ source(dataset_name, model_name) }}
    {% endif %}
  {% endif %}
{% endmacro %} #}

{% macro ref(model_name)%}
  {% if target.name == 'test' %}
    {% if model_name.startswith('seed') %}
      {{ builtins.ref(model_name) }}
    {% else %}
      {{ builtins.ref('test_' ~ model_name) }}
  {% else %}
    {{ builtins.ref(model_name) }}

{% macro source(dataset_name, model_name) %}
  {% if target.name == 'test' %}
    {{ builtins.ref('test_'|string + this.name) }}
  {% else %}
    {{ builtins.source(dataset_name, model_name) }}