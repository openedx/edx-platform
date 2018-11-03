{% macro header(resources) %}
<meta charset="utf-8" />
<title>{{ resources.notebook_id }}</title>

<script src="{{ resources.base_url }}/formgrader/static/components/jquery/jquery.min.js"></script>
<script src="{{ resources.base_url }}/formgrader/static/components/jquery-color/jquery.color.js"></script>
<script src="{{ resources.base_url }}/formgrader/static/components/underscore/underscore-min.js"></script>
<script src="{{ resources.base_url }}/formgrader/static/components/backbone/backbone-min.js"></script>
<script src="{{ resources.base_url }}/formgrader/static/components/bootstrap/js/bootstrap.min.js"></script>
<script type="text/javascript" src="{{ resources.base_url }}/formgrader/static/components/autosize/dist/autosize.min.js"></script>

<script type="text/javascript">
var submission_id = "{{ resources.submission_id }}";
var notebook_id = "{{ resources.notebook_id }}";
var assignment_id = "{{ resources.assignment_id }}";
var base_url = "{{ resources.base_url }}/formgrader";
</script>

<script src="{{ resources.base_url }}/formgrader/static/js/backbone_xsrf.js"></script>
<script src="{{ resources.base_url }}/formgrader/static/js/formgrade_keyboardmanager.js"></script>
<script src="{{ resources.base_url }}/formgrader/static/js/formgrade_models.js"></script>
<script src="{{ resources.base_url }}/formgrader/static/js/formgrade.js"></script>
<script type="text/javascript">
function toggle_name(on) {
  $(".name-shown").tooltip('hide');
  $(".name-hidden").tooltip('hide');
  if (on) {
    $(".name-shown").show();
    $(".name-hidden").hide();
  } else {
    $(".name-hidden").show();
    $(".name-shown").hide();
  }
}
</script>

<link rel="stylesheet" href="{{ resources.base_url }}/formgrader/static/components/bootstrap/css/bootstrap.min.css" />
{% endmacro %}

{% macro nav(resources) %}
  <nav class="navbar navbar-default navbar-fixed-top" role="navigation">
    <div class="container">
      <div class="col-md-2">
        <ul class="nav navbar-nav navbar-left">
          <li class="previous">
            <a data-toggle="tooltip" data-trigger="hover" data-placement="right" title="{{ resources.index }} remaining" href="{{ resources.base_url }}/formgrader/submissions/{{ resources.submission_id }}/prev">
            &larr; Prev
            </a>
          </li>
        </ul>
      </div>
      <div class="col-md-8">
        <ul class="nav text-center">
          <ul class="breadcrumb">
            <li><a href="{{ resources.base_url }}/formgrader/gradebook">Manual Grading</a></li>
            <li><a href="{{ resources.base_url }}/formgrader/gradebook/{{ resources.assignment_id }}">{{ resources.assignment_id }}</a></li>
            <li><a href="{{ resources.base_url }}/formgrader/gradebook/{{ resources.assignment_id }}/{{ resources.notebook_id }}">{{ resources.notebook_id }}</a></li>
            <li class="active live-notebook">
              <a class="name-hidden" data-toggle="tooltip" data-placement="bottom" title="Open live notebook" target="_blank" href="{{ resources.base_url }}/notebooks/{{ resources.notebook_path }}">
                Submission #{{ resources.index + 1 }}
              </a>
              <a class="name-shown" data-toggle="tooltip" data-placement="bottom" title="Open live notebook" target="_blank" href="{{ resources.base_url }}/notebooks/{{ resources.notebook_path }}">
                {%- if resources.last_name and resources.first_name -%}
                {{ resources.last_name }}, {{ resources.first_name }}
                {%- else -%}
                {{ resources.student }}
                {%- endif -%}
              </a>
              <span class="glyphicon glyphicon-eye-open name-hidden" aria-hidden="true" onclick="toggle_name(true);"></span>
              <span class="glyphicon glyphicon-eye-close name-shown" aria-hidden="true" onclick="toggle_name(false);"></span>
            </li>
          </ul>
        </ul>
      </div>
      <div class="col-md-2">
        <ul class="nav navbar-nav navbar-right">
          <li class="next">
            <a class="tabbable" data-trigger="hover" data-toggle="tooltip" data-placement="left" title="{{ resources.total - (resources.index + 1) }} remaining" href="{{ resources.base_url }}/formgrader/submissions/{{ resources.submission_id }}/next">
            Next &rarr;
            </a>
          </li>
        </ul>
      </div>
    </div>
    </div>
  </nav>
  <script type="text/javascript">
  $('span.glyphicon.name-hidden').tooltip({title: "Show student name", placement: "bottom", trigger: "hover"});
  $('span.glyphicon.name-shown').tooltip({title: "Hide student name", placement: "bottom", trigger: "hover"});
  </script>
{% endmacro %}