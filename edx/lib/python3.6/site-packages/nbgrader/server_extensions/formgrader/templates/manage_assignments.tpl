{%- extends 'base.tpl' -%}

{%- block head -%}
<script>
var url_prefix = "{{ url_prefix }}";
</script>

<script src="{{ base_url }}/formgrader/static/js/manage_assignments.js"></script>
{%- endblock -%}

{%- block title -%}
Manage Assignments
{%- endblock -%}

{%- block sidebar -%}
<li role="presentation" class="active"><a href="{{ base_url }}/formgrader/manage_assignments">Manage Assignments</a></li>
<li role="presentation"><a href="{{ base_url }}/formgrader/gradebook">Manual Grading</a></li>
<li role="presentation"><a href="{{ base_url }}/formgrader/manage_students">Manage Students</a></li>
{%- endblock -%}

{%- block breadcrumbs -%}
<ol class="breadcrumb">
  <li class="active">Assignments</li>
</ol>
{%- endblock -%}

{%- block messages -%}
<div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">
  <div class="panel panel-default">
    <div class="panel-heading" role="tab" id="headingOne">
      <h4 class="panel-title">
        <a class="collapsed" role="button" data-toggle="collapse" data-parent="#accordion" href="#collapseOne" aria-expanded="false" aria-controls="collapseOne">
          Instructions (click to expand)
        </a>
      </h4>
    </div>
    <div id="collapseOne" class="panel-collapse collapse" role="tabpanel" aria-labelledby="headingOne">
      <div class="panel-body">
        <ol>
          <li>To <b>create</b> an assignment, click the "Add new assignment..." button below.</li>
          <li>To <b>edit assignment files</b>, click on the name of an assignment.</li>
          <li>To <b>edit the assignment metadata</b>, click on the edit button.</li>
          <li>To <b>generate</b> the student version of an assignment, click on the generate button.</li>
          <li>To <b>preview</b> the student version of an assignment, click on the preview button.</li>
          <li><i>(JupyterHub only)</i> To <b>release</b> the assignment to students, click the release button.
          You can "unrelease" an assignment by clicking again, though note some students may have
          already accessed the assignment. <b>Note</b> that for the release button to become
          available, the <code>course_id</code> option must be set in <code>nbgrader_config.py</code>.
          For details, see <a href="http://nbgrader.readthedocs.io/en/stable/configuration/config_options.html">the documentation</a>.</li>
          <li><i>(JupyterHub only)</i> To <b>collect</b> assignments, click the collect button.</li>
          <li>To <b>autograde</b> submissions, click on the number of collected submissions. You must run
          the autograder on the submissions before you can manually grade them.</li>
        </ol>
      </div>
    </div>
  </div>
</div>
{% if windows %}
<div class="alert alert-warning" id="warning-windows">
Windows operating system detected. Please note that the "release" and "collect"
functionality will not be available.
</div>
{% elif exchange_missing %}
<div class="alert alert-warning" id="warning-exchange">
The exchange directory at <code>{{ exchange }}</code> does not exist and could
not be created. The "release" and "collect" functionality will not be available.
Please see the documentation on
<a href="http://nbgrader.readthedocs.io/en/stable/user_guide/managing_assignment_files.html#setting-up-the-exchange">Setting Up The Exchange</a>
for instructions.
</div>
{% elif not course_id %}
<div class="alert alert-warning" id="warning-course-id">
The course id has not been set in <code>nbgrader_config.py</code>. The "release"
and "collect" functionality will not be available. Please see the documentation on
<a href="http://nbgrader.readthedocs.io/en/stable/user_guide/managing_assignment_files.html#setting-up-the-exchange">Setting Up The Exchange</a>
for instructions.
</div>
{% endif %}
{%- endblock -%}

{%- block table_header -%}
<tr>
  <th>Name</th>
  <th class="text-center">Due Date</th>
  <th class="text-center">Status</th>
  <th class="text-center no-sort">Edit</th>
  <th class="text-center no-sort">Generate</th>
  <th class="text-center no-sort">Preview</th>
  <th class="text-center no-sort">Release</th>
  <th class="text-center no-sort">Collect</th>
  <th class="text-center"># Submissions</th>
</tr>
{%- endblock -%}

{%- block table_body -%}
<tr><td colspan="9">Loading, please wait...</td></tr>
{%- endblock -%}

{%- block table_footer -%}
<tr>
  <td colspan="9">
    <span class="glyphicon glyphicon-plus" aria-hidden="true"></span>
    <a href="#" onClick="createAssignmentModal();">Add new assignment...</a>
  </td>
</tr>
{%- endblock -%}
