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
      {{ builtins.ref(model_name).include(database=false) }}
    {% else %}
      {{ builtins.ref('test_' ~ model_name).include(database=false) }}
    {% endif %}
  {% else %}
    {{ builtins.ref(model_name).include(database=false) }}
  {% endif %}
{% endmacro %}


{% macro source(dataset_name, model_name) %}
  {% if target.name == 'test' %}
    {{ builtins.ref('test_'|string + this.name).include(database=false) }}
  {% else %}
    {{ builtins.source(dataset_name, model_name) }}
  {% endif %}
{% endmacro %}


{# {% macro refv2(model_name)%}
  {% if target.name == 'test' %}
    {% if model_name.startswith('seed') %}
      {{ ref(model_name) }}
    {% else %}
      {{ ref('test_' ~ model_name) }}
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
 #}
