define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    './assignment_list'
], function(Jupyter, $, utils, AssignmentList) {
    "use strict";

    var nbgrader_version = "0.5.4";

    var ajax = utils.ajax || $.ajax;
    // Notebook v4.3.1 enabled xsrf so use notebooks ajax that includes the
    // xsrf token in the header data

    var assignment_html = $([
        '<div id="assignments" class="tab-pane">',
        '  <div id="assignments_toolbar" class="row list_toolbar">',
        '    <div class="col-sm-8 no-padding">',
        '      <span id="assignments_list_info" class="toolbar_info">Released, downloaded, and submitted assignments for course:</span>',
        '      <div class="btn-group btn-group-xs">',
        '        <button type="button" class="btn btn-default" id="course_list_default">Loading, please wait...</button>',
        '        <button type="button" class="btn btn-default dropdown-toggle" id="course_list_dropdown" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" disabled="disabled">',
        '          <span class="caret"></span>',
        '          <span class="sr-only">Toggle Dropdown</span>',
        '        </button>',
        '        <ul class="dropdown-menu" id="course_list">',
        '        </ul>',
        '      </div>',
        '    </div>',
        '    <div class="col-sm-4 no-padding tree-buttons">',
        '      <span id="assignments_buttons" class="pull-right toolbar_buttons">',
        '      <button id="refresh_assignments_list" title="Refresh assignments list" class="btn btn-default btn-xs"><i class="fa fa-refresh"></i></button>',
        '      </span>',
        '    </div>',
        '  </div>',
        '  <div class="alert alert-danger version_error">',
        '  </div>',
        '  <div class="panel-group">',
        '    <div class="panel panel-default">',
        '      <div class="panel-heading">',
        '        Released assignments',
        '      </div>',
        '      <div class="panel-body">',
        '        <div id="released_assignments_list" class="list_container">',
        '          <div id="released_assignments_list_placeholder" class="row list_placeholder">',
        '            <div> There are no assignments to fetch. </div>',
        '          </div>',
        '          <div id="released_assignments_list_loading" class="row list_loading">',
        '            <div> Loading, please wait... </div>',
        '          </div>',
        '          <div id="released_assignments_list_error" class="row list_error">',
        '            <div></div>',
        '          </div>',
        '        </div>',
        '      </div>',
        '    </div>',
        '    <div class="panel panel-default">',
        '      <div class="panel-heading">',
        '        Downloaded assignments',
        '      </div>',
        '      <div class="panel-body">',
        '        <div id="fetched_assignments_list" class="list_container" role="tablist" aria-multiselectable="true">',
        '          <div id="fetched_assignments_list_placeholder" class="row list_placeholder">',
        '            <div> There are no downloaded assignments. </div>',
        '          </div>',
        '          <div id="fetched_assignments_list_loading" class="row list_loading">',
        '            <div> Loading, please wait... </div>',
        '          </div>',
        '          <div id="fetched_assignments_list_error" class="row list_error">',
        '            <div></div>',
        '          </div>',
        '        </div>',
        '      </div>',
        '    </div>',
        '    <div class="panel panel-default">',
        '      <div class="panel-heading">',
        '        Submitted assignments',
        '      </div>',
        '      <div class="panel-body">',
        '        <div id="submitted_assignments_list" class="list_container">',
        '          <div id="submitted_assignments_list_placeholder" class="row list_placeholder">',
        '            <div> There are no submitted assignments. </div>',
        '          </div>',
        '          <div id="submitted_assignments_list_loading" class="row list_loading">',
        '            <div> Loading, please wait... </div>',
        '          </div>',
        '          <div id="submitted_assignments_list_error" class="row list_error">',
        '            <div></div>',
        '          </div>',
        '        </div>',
        '      </div>',
        '    </div>',
        '  </div>   ',
        '</div>'
    ].join('\n'));

    function checkNbGraderVersion(base_url) {
        var settings = {
            cache : false,
            type : "GET",
            dataType : "json",
            data : {
                version: nbgrader_version
            },
            success : function (response) {
                if (!response['success']) {
                    var err = $("#assignments .version_error");
                    err.text(response['message']);
                    err.show();
                }
            },
            error : utils.log_ajax_error,
        };
        var url = utils.url_path_join(base_url, 'nbgrader_version');
        ajax(url, settings);
    }

    function load() {
        if (!Jupyter.notebook_list) return;
        var base_url = Jupyter.notebook_list.base_url;
        $('head').append(
            $('<link>')
            .attr('rel', 'stylesheet')
            .attr('type', 'text/css')
            .attr('href', base_url + 'nbextensions/assignment_list/assignment_list.css')
        );
        $(".tab-content").append(assignment_html);
        $("#tabs").append(
            $('<li>')
            .append(
                $('<a>')
                .attr('href', '#assignments')
                .attr('data-toggle', 'tab')
                .text('Assignments')
                .click(function (e) {
                    window.history.pushState(null, null, '#assignments');
                    course_list.load_list();
                })
            )
        );
        var assignment_list = new AssignmentList.AssignmentList(
            '#released_assignments_list',
            '#fetched_assignments_list',
            '#submitted_assignments_list',
            {
                base_url: Jupyter.notebook_list.base_url,
                notebook_path: Jupyter.notebook_list.notebook_path,
            }
        );
        var course_list = new AssignmentList.CourseList(
            '#course_list',
            '#course_list_default',
            '#course_list_dropdown',
            '#refresh_assignments_list',
            assignment_list,
            {
                base_url: Jupyter.notebook_list.base_url,
            }
        );
        checkNbGraderVersion(base_url);
    }
    return {
        load_ipython_extension: load
    };
});
