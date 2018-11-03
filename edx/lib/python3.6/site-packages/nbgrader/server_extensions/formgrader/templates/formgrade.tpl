{%- extends 'basic.tpl' -%}
{% from 'formgrade_macros.tpl' import nav, header %}

{%- block header -%}
<!DOCTYPE html>
<html>
<head>
{{ header(resources) }}

{% for css in resources.inlining.css -%}
    <style type="text/css">
    {{ css }}
    </style>
{% endfor %}

<!-- MathJax -->
<script type="text/javascript">
window.MathJax = {
    tex2jax: {
        inlineMath: [ ['$','$'], ["\\(","\\)"] ],
        displayMath: [ ['$$','$$'], ["\\[","\\]"] ],
        processEscapes: true,
        processEnvironments: true
    },
    // Center justify equations in code and markdown cells. Elsewhere
    // we use CSS to left justify single line equations in code cells.
    displayAlign: 'center',
    "HTML-CSS": {
        styles: {'.MathJax_Display': {"margin": 0}},
        linebreaks: { automatic: true }
    }
};
</script>

<script type="text/javascript" src="{{ resources.base_url }}/{{ resources.mathjax_url }}?config=TeX-AMS-MML_HTMLorMML-full"></script>

<link rel="stylesheet" href="{{ resources.base_url }}/formgrader/static/css/formgrade.css" />

</head>
{%- endblock header -%}

{% block body %}
<body>
  {{ nav(resources) }}
  <div class="container">
    <div class="panel panel-default">
      <div class="panel-heading">
        <h4 class="panel-title">
          <span>{{ resources.notebook_id }}</span>
          <span class="pull-right">Submission {{ resources.index + 1 }} / {{ resources.total }}</span>
        </h4>
      </div>
      <div class="panel-body">
        <div id="notebook" class="border-box-sizing">
          <div class="container" id="notebook-container">
            {{ super() }}
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="help"><span class="glyphicon glyphicon-question-sign"></span></div>
  <div id="statusmessage"></div>
</body>
{%- endblock body %}

{% block footer %}
</html>
{% endblock footer %}

{% macro score(cell) -%}
  <span class="glyphicon glyphicon-ok save-icon score-saved"></span>
  <div class="pull-right">
    <span class="btn-group btn-group-sm scoring-buttons" role="group">
      <button type="button" class="btn btn-warning mark-graded">Resolve</button>
      <button type="button" class="btn btn-success full-credit">Full credit</button>
      <button type="button" class="btn btn-danger no-credit">No credit</button>
    </span>
    <span>
      <input class="score tabbable" id="{{ cell.metadata.nbgrader.grade_id }}" style="width: 4em;" type="number" /> / {{ cell.metadata.nbgrader.points | float | round(2) }}
    </span>
    <span style="margin-left: 1em;">
      + <input class="extra-credit tabbable" id="{{ cell.metadata.nbgrader.grade_id }}_extra_credit" style="width: 3em;" type="number" /> (extra credit)
    </span>
  </div>
{%- endmacro %}


{% macro nbgrader_heading(cell) -%}
<div class="panel-heading">
{%- if cell.metadata.nbgrader.solution -%}
  <span class="nbgrader-label">Student's answer</span>
  <span class="glyphicon glyphicon-ok comment-saved save-icon"></span>
  {%- if cell.metadata.nbgrader.grade -%}
  {{ score(cell) }}
  {%- endif -%}
{%- elif cell.metadata.nbgrader.grade -%}
  <span class="nbgrader-label"><code>{{ cell.metadata.nbgrader.grade_id }}</code></span>
  {{ score(cell) }}
{%- endif -%}
</div>  
{%- endmacro %}

{% macro nbgrader_footer(cell) -%}
{%- if cell.metadata.nbgrader.solution -%}
<div class="panel-footer">
  <div><textarea id="{{ cell.metadata.nbgrader.grade_id }}-comment" class="comment tabbable"></textarea></div>
</div>
{%- endif -%}
{%- endmacro %}

{% block markdowncell scoped %}
<div class="cell border-box-sizing text_cell rendered">
  {{ self.empty_in_prompt() }}

  {%- if 'nbgrader' in cell.metadata and (cell.metadata.nbgrader.solution or cell.metadata.nbgrader.grade) -%}
  <div class="panel panel-primary nbgrader_cell">
    {{ nbgrader_heading(cell) }}
    <div class="panel-body">
      <div class="text_cell_render border-box-sizing rendered_html">
        {{ cell.source  | markdown2html | strip_files_prefix }}
      </div>
    </div>
    {{ nbgrader_footer(cell) }}
  </div>

  {%- else -%}

  <div class="inner_cell">
    <div class="text_cell_render border-box-sizing rendered_html">
      {{ cell.source  | markdown2html | strip_files_prefix }}
    </div>
  </div>

  {%- endif -%}

</div>
{% endblock markdowncell %}

{% block input %}
  {%- if 'nbgrader' in cell.metadata and (cell.metadata.nbgrader.solution or cell.metadata.nbgrader.grade) -%}
  <div class="panel panel-primary nbgrader_cell">
    {{ nbgrader_heading(cell) }}
    <div class="panel-body">
      <div class="input_area">
        {{ cell.source | highlight_code(metadata=cell.metadata) }}
      </div>
    </div>
    {{ nbgrader_footer(cell) }}
  </div>

  {%- else -%}
  
  <div class="inner_cell">
    <div class="input_area">
      {{ cell.source | highlight_code(metadata=cell.metadata) }}
    </div>
  </div>
  {%- endif -%}

{% endblock input %}
