<!doctype html>
<head>
  <title>nbgrader formgrade</title>

  <script src="{{ base_url }}/formgrader/static/components/jquery/jquery.min.js"></script>
  <script src="{{ base_url }}/formgrader/static/components/underscore/underscore-min.js"></script>
  <script src="{{ base_url }}/formgrader/static/components/backbone/backbone-min.js"></script>
  <script src="{{ base_url }}/formgrader/static/components/bootstrap/js/bootstrap.min.js"></script>
  <script src="{{ base_url }}/formgrader/static/components/datatables.net/js/jquery.dataTables.min.js"></script>
  <script src="{{ base_url }}/formgrader/static/components/datatables.net-bs/js/dataTables.bootstrap.min.js"></script>
  <script src="{{ base_url }}/formgrader/static/js/backbone_xsrf.js"></script>
  <script src="{{ base_url }}/formgrader/static/js/utils.js"></script>

  <link rel="stylesheet" href="{{ base_url }}/formgrader/static/components/bootstrap/css/bootstrap.min.css" />
  <link rel="stylesheet" href="{{ base_url }}/formgrader/static/components/datatables.net-bs/css/dataTables.bootstrap.min.css">
  <link rel="stylesheet" href="{{ base_url }}/formgrader/static/css/nbgrader.css">

  <script>
  var base_url = "{{ base_url }}";
  </script>

  {%- block head -%}
  {%- endblock -%}
</head>

<body>
  <div class="container-fluid">
    <div class="row">
      <div class="col-md-2">
        <div class="page-header">
          <h1>nbgrader</h1>
        </div>
      </div>
      <div class="col-md-8">
        <div class="page-header">
          <h1>
          {%- block title -%}
          {%- endblock -%}
          </h1>
        </div>
      </div>
      <div class="col-md-2">
        <div class="pull-right jupyter-logo">
          <svg viewBox="0 0 440 440" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%">
            <g fill="#414042">
              <path d="M60.9 232c0 12.7-1 16.9-3.6 20-2.3 2.5-6.1 3.7-10.5 4.1l1 7.6c5.2 0 12.2-1.8 16.5-6 4.7-4.8 6.4-11.5 6.4-21.9v-48.2H61V232zM133.1 226.2c0 5.5.1 10.3.4 14.5h-8.6l-.5-8.7h-.2c-2.5 4.3-8.1 9.9-17.6 9.9-8.3 0-18.3-4.6-18.3-23.3v-31.1H98V217c0 10.1 3.1 16.9 11.9 16.9 6.5 0 11-4.5 12.7-8.8.5-1.4.9-3.2.9-4.9v-32.6h9.7v38.6zM151.3 204.9c0-6.8-.2-12.3-.4-17.3h8.7l.4 9.1h.2c4-6.5 10.2-10.3 18.9-10.3 12.8 0 22.5 10.9 22.5 27 0 19.1-11.6 28.5-24.2 28.5-7 0-13.2-3.1-16.4-8.3h-.2v28.9h-9.6v-57.6zm9.5 14.2c0 1.4.2 2.7.4 4 1.8 6.7 7.6 11.3 14.5 11.3 10.2 0 16.1-8.3 16.1-20.5 0-10.7-5.6-19.8-15.8-19.8-6.6 0-12.7 4.7-14.6 12-.3 1.2-.7 2.6-.7 4v9zM218.7 187.6l11.6 31.4c1.2 3.5 2.5 7.7 3.4 10.9h.2c1-3.2 2.1-7.2 3.4-11.1l10.5-31.2H258l-14.5 37.9c-6.9 18.2-11.6 27.6-18.2 33.3-4.7 4.2-9.4 5.8-11.9 6.3L211 257c2.4-.8 5.6-2.3 8.5-4.7 2.6-2.1 5.9-5.8 8.1-10.8.4-1 .8-1.8.8-2.3 0-.5-.2-1.3-.7-2.5l-19.7-49h10.7zM283.5 172.3v15.3h13.8v7.4h-13.8v28.7c0 6.6 1.9 10.3 7.2 10.3 2.5 0 4.4-.3 5.6-.7l.4 7.2c-1.9.8-4.8 1.3-8.6 1.3-4.5 0-8.1-1.4-10.4-4.1-2.7-2.9-3.7-7.6-3.7-13.8v-29h-8.2v-7.4h8.2v-12.7l9.5-2.5zM315.2 215.9c.2 13.1 8.6 18.4 18.2 18.4 6.9 0 11.1-1.2 14.7-2.7l1.6 6.9c-3.4 1.5-9.2 3.3-17.7 3.3-16.4 0-26.1-10.8-26.1-26.8s9.4-28.7 24.9-28.7c17.3 0 22 15.3 22 25 0 2-.2 3.5-.3 4.5h-37.3zm28.3-6.9c.1-6.1-2.5-15.7-13.4-15.7-9.8 0-14.1 9-14.8 15.7h28.2zM367 204.1c0-6.3-.1-11.6-.4-16.6h8.5l.3 10.4h.4c2.4-7.1 8.2-11.6 14.7-11.6 1.1 0 1.9.1 2.7.3v9.1c-1-.2-2-.3-3.3-.3-6.8 0-11.6 5.2-13 12.4-.2 1.3-.4 2.9-.4 4.5v28.3H367v-36.5z"/>
            </g>
            <circle cx="329.8" cy="40.6" fill="#6D6E71" r="21.4"/>
            <linearGradient gradientUnits="userSpaceOnUse" id="a" x1="67.752" x2="372.271" y1="321.544" y2="321.544">
              <stop offset=".052" stop-color="#F78D26"/>
              <stop offset=".206" stop-color="#F68826"/>
              <stop offset=".432" stop-color="#F37A25"/>
              <stop offset=".477" stop-color="#F37625"/>
              <stop offset=".616" stop-color="#E76623"/>
              <stop offset=".836" stop-color="#DC5221"/>
              <stop offset=".987" stop-color="#D84B21"/>
            </linearGradient>
            <path d="M220 326.4c-65.5 0-122.6-23.5-152.3-58.3C90.2 330.4 149.9 375 220 375s129.8-44.6 152.3-106.9c-29.7 34.8-86.8 58.3-152.3 58.3z" fill="url(#a)"/>
            <linearGradient gradientUnits="userSpaceOnUse" id="b" x1="67.752" x2="372.271" y1="104.869" y2="104.869">
              <stop offset=".052" stop-color="#F78D26"/>
              <stop offset=".206" stop-color="#F68826"/>
              <stop offset=".432" stop-color="#F37A25"/>
              <stop offset=".477" stop-color="#F37625"/>
              <stop offset=".616" stop-color="#E76623"/>
              <stop offset=".836" stop-color="#DC5221"/><stop offset=".987" stop-color="#D84B21"/>
            </linearGradient>
            <path d="M220 100c65.5 0 122.6 23.5 152.3 58.3C349.8 96 290.1 51.4 220 51.4S90.2 96 67.8 158.3C97.5 123.6 154.5 100 220 100z" fill="url(#b)"/>
            <circle cx="110.5" cy="394.4" fill="#939598" r="25.8"/>
            <circle cx="85.1" cy="70" fill="#58595B" r="15.7"/>
          </svg>
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col-md-2">
        <ul class="nav nav-pills nav-stacked">
          {%- block sidebar -%}
          <li role="presentation"><a href="{{ base_url }}/formgrader/manage_assignments">Manage Assignments</a></li>
          <li role="presentation"><a href="{{ base_url }}/formgrader/gradebook">Gradebook</a></li>
          <li role="presentation"><a href="{{ base_url }}/formgrader/manage_students">Manage Students</a></li>
          {%- endblock -%}
        </ul>
      </div>
      <div class="col-md-10">
        {%- block body -%}
        {%- block breadcrumbs -%}
        {%- endblock -%}
        {%- block messages -%}
        {%- endblock -%}
        <table class="table table-hover">
          <thead>
            {%- block table_header -%}
            {%- endblock -%}
          </thead>
          <tbody id="main-table">
            {%- block table_body -%}
            {%- endblock -%}
          </tbody>
          <tfoot>
            {%- block table_footer -%}
            {%- endblock -%}
          </tfoot>
        </table>
        {%- endblock -%}
      </div>
    </div>
  </div>
  {%- block script -%}
  {%- endblock -%}
</body>
