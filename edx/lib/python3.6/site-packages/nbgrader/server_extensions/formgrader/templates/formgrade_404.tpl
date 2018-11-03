{% from 'formgrade_macros.tpl' import nav, header %}

<!DOCTYPE html>
<html>
<head>
{{ header(resources) }}
<link rel="stylesheet" href="{{ resources.base_url }}/formgrader/static/css/formgrade.css" />
</head>

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
            Error: Submission notebook file not found: {{ resources.filename }}
          </div>
        </div>
      </div>
    </div>
  </div>
</body>

</html>
