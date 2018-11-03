{%- extends 'manage_students_base.tpl' -%}

{%- block head -%}
<script src="{{ base_url }}/formgrader/static/js/manage_students.js"></script>
{%- endblock -%}

{%- block breadcrumbs -%}
<ol class="breadcrumb">
  <li class="active">Students</li>
</ol>
{%- endblock -%}

{%- block table_header -%}
<tr>
  <th>Name</th>
  <th class="text-center">Student ID</th>
  <th class="text-center">Email</th>
  <th class="text-center">Overall Score</th>
  <th class="text-center no-sort">Edit Student</th>
</tr>
{%- endblock -%}

{%- block table_body -%}
<tr><td colspan="5">Loading, please wait...</td></tr>
{%- endblock -%}

{%- block table_footer -%}
<tr>
  <td colspan="5">
    <span class="glyphicon glyphicon-plus" aria-hidden="true"></span>
    <a href="#" onClick="createStudentModal();">Add new student...</a>
  </td>
</tr>
{%- endblock -%}