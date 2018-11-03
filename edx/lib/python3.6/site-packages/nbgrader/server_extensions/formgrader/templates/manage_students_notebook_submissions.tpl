{%- extends 'manage_students_base.tpl' -%}

{%- block head -%}
<script>
var student_id = "{{ student_id }}";
var assignment_id = "{{ assignment_id }}";
</script>

<script src="{{ base_url }}/formgrader/static/js/manage_students_notebook_submissions.js"></script>
{%- endblock head -%}

{%- block breadcrumbs -%}
<ol class="breadcrumb">
  <li><a href="{{ base_url }}/formgrader/manage_students">Students</a></li>
  <li><a href="{{ base_url }}/formgrader/manage_students/{{ student_id }}">{{ student_id }}</a></li>
  <li class="active">{{ assignment_id }}</li>
</ol>
{%- endblock -%}

{%- block table_header -%}
<tr>
  <th>Notebook ID</th>
  <th class="text-center">Overall Score</th>
  <th class="text-center">Code Score</th>
  <th class="text-center">Written Score</th>
  <th class="text-center">Needs manual grade?</th>
  <th class="text-center">Tests failed?</th>
  <th class="text-center">Flagged?</th>
</tr>
{%- endblock -%}

{%- block table_body -%}
<tr><td colspan="7">Loading, please wait...</td></tr>
{%- endblock -%}
