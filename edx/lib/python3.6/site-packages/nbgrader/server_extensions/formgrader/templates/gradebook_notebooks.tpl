{%- extends 'gradebook_base.tpl' -%}

{%- block head -%}
<script>
var assignment_id = "{{ assignment_id }}";
</script>

<script src="{{ base_url }}/formgrader/static/js/gradebook_notebooks.js"></script>
{%- endblock head -%}

{%- block breadcrumbs -%}
<ol class="breadcrumb">
  <li><a href="{{ base_url }}/formgrader/gradebook">Manual Grading</a></li>
  <li class="active">{{ assignment_id }}</li>
</ol>
{%- endblock -%}

{%- block table_header -%}
<tr>
  <th>Notebook ID</th>
  <th class="text-center">Avg. Score</th>
  <th class="text-center">Avg. Code Score</th>
  <th class="text-center">Avg. Written Score</th>
  <th class="text-center">Needs Manual Grade?</th>
</tr>
{%- endblock -%}

{%- block table_body -%}
<tr><td colspan="5">Loading, please wait...</td></tr>
{%- endblock -%}
