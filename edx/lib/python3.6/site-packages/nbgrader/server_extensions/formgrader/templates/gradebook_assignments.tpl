{%- extends 'gradebook_base.tpl' -%}

{%- block head -%}
<script src="{{ base_url }}/formgrader/static/js/gradebook_assignments.js"></script>
{%- endblock -%}

{%- block breadcrumbs -%}
<ol class="breadcrumb">
  <li class="active">Manual Grading</li>
</ol>
{%- endblock -%}

{%- block table_header -%}
<tr>
  <th>Assignment ID</th>
  <th class="text-center">Due Date</th>
  <th class="text-center">Submissions</th>
  <th class="text-center">Score</th>
</tr>
{%- endblock -%}

{%- block table_body -%}
<tr><td colspan="4">Loading, please wait...</td></tr>
{%- endblock -%}
