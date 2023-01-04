{% macro select_table(source_table, test_table) %}

      {% if var('unit_test', false) == true %}
            
            {{ return(test_table) }}

      {% else %}

            {{ return(source_table) }}

      {% endif %}

{% endmacro %}