{%- extends 'manage_students_base.tpl' -%}

{%- block head -%}
<script>
var student_id = "{{ student_id }}";
</script>

<script src="{{ base_url }}/formgrader/static/js/manage_students_assignments.js"></script>
{%- endblock head -%}

{%- block breadcrumbs -%}
<ol class="breadcrumb">
  <li><a href="{{ base_url }}/formgrader/manage_students">Students</a></li>
  <li class="active">{{ student_id }}</li>
</ol>
{%- endblock -%}

{%- block table_header -%}
<tr>
  <th>Assignment ID</th>
  <th class="text-center">Overall Score</th>
  <th class="text-center">Code Score</th>
  <th class="text-center">Written Score</th>
  <th class="text-center">Needs Manual Grade?</th>
</tr>
{%- endblock -%}

{%- block table_body -%}
<tr><td colspan="5">Loading, please wait...</td></tr>
{%- endblock -%}
