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