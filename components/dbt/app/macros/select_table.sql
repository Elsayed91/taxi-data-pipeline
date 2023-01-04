{# {% macro select_table(source_table, test_table) %}

      {% if target.name == 'test' %}
            
            {{ return(test_table) }}

      {% else %}

            {{ return(source_table) }}

      {% endif %}

{% endmacro %} #}

{# {% set src = select_table(source("staging_data", "yellow_staging"), ref('test_dbt__ml__yellow_fare')) %} #}