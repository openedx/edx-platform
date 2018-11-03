{%- extends 'base.tpl' -%}

{%- block title -%}
Not Authorized
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
Sorry, you are not authorized to access the formgrader.
<span id="error-{{ error_code }}"></span>
</div>
{%- endblock -%}