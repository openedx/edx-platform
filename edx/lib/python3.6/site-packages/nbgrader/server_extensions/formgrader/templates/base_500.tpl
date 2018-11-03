{%- extends 'base.tpl' -%}

{%- block title -%}
Error
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
Sorry, the formgrader encountered an error. Please contact the administrator of
the formgrader for further assistance.
<span id="error-{{ error_code }}"></span>
</div>
{%- endblock -%}