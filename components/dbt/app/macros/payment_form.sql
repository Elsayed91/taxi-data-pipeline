{% macro payment_form(payment_type) -%}
    case
        when {{ payment_type }}=1 then 'Credit card'
        when {{ payment_type }}=2 then 'Cash'
        when {{ payment_type }}=3 then 'No charge'
        when {{ payment_type }}=4 then 'Dispute'
        when {{ payment_type }}=5 then 'Unknown'
        when {{ payment_type }}=6 then 'Voided trip'
    end
{%- endmacro %}