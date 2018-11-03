define([
    'jquery',
    'base/js/namespace',
    'base/js/dialog',
    'base/js/utils'

], function ($, Jupyter, dialog, utils) {
    "use strict";

    var nbgrader_version = "0.5.4";

    var ajax = utils.ajax || $.ajax;
    // Notebook v4.3.1 enabled xsrf so use notebooks ajax that includes the
    // xsrf token in the header data

    var checkNbGraderVersion = function (callback) {
        var settings = {
            cache : false,
            type : "GET",
            dataType : "json",
            data : {
                version: nbgrader_version
            },
            success : function (response) {
                if (!response['success']) {
                    var body = $("<div/>").text(response['message']);
                    dialog.modal({
                        title: "Version Mismatch",
                        body: body,
                        buttons: { OK: { class : "btn-primary" } }
                    });
                } else {
                    callback();
                }
            },
            error : utils.log_ajax_error,
        };
        var url = utils.url_path_join(Jupyter.notebook.base_url, 'nbgrader_version');
        ajax(url, settings);
    };

    var add_button = function () {
        var maintoolbar = $("#maintoolbar-container");
        var btn_group = $("<div />").attr("class", "btn-group")
        var btn = $("<button />").attr("class", "btn btn-default validate").text("Validate");
        btn_group.append(btn)
        maintoolbar.append(btn_group);

        btn.click(function (e) {
            checkNbGraderVersion(function () {
                var p = Jupyter.notebook.save_notebook();
                p.then(function () {
                    var settings = {
                        cache : false,
                        data : { path: Jupyter.notebook.notebook_path },
                        type : "POST",
                        dataType : "json",
                        success : function (data, status, xhr) {
                            btn.text('Validate');
                            btn.removeAttr('disabled');
                            validate(data, btn);
                        },
                        error : function (xhr, status, error) {
                            utils.log_ajax_error(xhr, status, error);
                        }
                    };
                    btn.text('Validating...');
                    btn.attr('disabled', 'disabled');
                    var url = utils.url_path_join(
                        Jupyter.notebook.base_url,
                        'assignments',
                        'validate'
                    );
                    ajax(url, settings);
                });
            });
        });
    };

    var validate = function (data, button) {
        var body = $('<div/>').attr("id", "validation-message");
        if (data.success === true) {
            if (typeof(data.value) === "string") {
                data = JSON.parse(data.value);
            } else {
                data = data.value;
            }
            if (data.changed !== undefined) {
                for (var i=0; i<data.changed.length; i++) {
                    body.append($('<div/>').append($('<p/>').text('The source of the following cell has changed, but it should not have!')));
                    body.append($('<pre/>').text(data.changed[i].source));
                }
                body.addClass("validation-changed");

            } else if (data.passed !== undefined) {
                for (var i=0; i<data.changed.length; i++) {
                    body.append($('<div/>').append($('<p/>').text('The following cell passed:')));
                    body.append($('<pre/>').text(data.passed[i].source));
                }
                body.addClass("validation-passed");

            } else if (data.failed !== undefined) {
                for (var i=0; i<data.failed.length; i++) {
                    body.append($('<div/>').append($('<p/>').text('The following cell failed:')));
                    body.append($('<pre/>').text(data.failed[i].source));
                    body.append($('<pre/>').html(data.failed[i].error));
                }
                body.addClass("validation-failed");

            } else {
                body.append($('<div/>').append($('<p/>').text('Success! Your notebook passes all the tests.')));
                body.addClass("validation-success");
            }

        } else {
            body.append($('<div/>').append($('<p/>').text('There was an error running the validate command:')));
            body.append($('<pre/>').text(data.value));
        }

        dialog.modal({
            title: "Validation Results",
            body: body,
            buttons: { OK: { class : "btn-primary" } }
        });
    };

    var load_extension = function () {
        add_button();
        console.log('nbgrader extension for validating notebooks loaded.');
    };

    return {
        'load_ipython_extension': load_extension
    };
});