// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'base/js/dialog',
], function(Jupyter, $, utils, dialog) {
    "use strict";

    var ajax = utils.ajax || $.ajax;
    // Notebook v4.3.1 enabled xsrf so use notebooks ajax that includes the
    // xsrf token in the header data

    var CourseList = function (course_list_selector, default_course_selector, dropdown_selector, refresh_selector, assignment_list, options) {
        this.course_list_selector = course_list_selector;
        this.default_course_selector = default_course_selector;
        this.dropdown_selector = course_list_dropdown;
        this.refresh_selector = refresh_selector;

        this.course_list_element = $(course_list_selector);
        this.default_course_element = $(default_course_selector);
        this.dropdown_element = $(dropdown_selector);
        this.refresh_element = $(refresh_selector);

        this.assignment_list = assignment_list;
        this.current_course = undefined;
        this.bind_events()

        options = options || {};
        this.options = options;
        this.base_url = options.base_url || utils.get_body_data("baseUrl");

        this.data = undefined;
    };

    CourseList.prototype.bind_events = function () {
        var that = this;
        this.refresh_element.click(function () {
            that.load_list();
        });
    };


    CourseList.prototype.enable_list = function () {
        this.dropdown_element.removeAttr("disabled");
    };


    CourseList.prototype.disable_list = function () {
        this.dropdown_element.attr("disabled", "disabled");
    };


    CourseList.prototype.clear_list = function () {
        // remove list items
        this.course_list_element.children('li').remove();
    };


    CourseList.prototype.load_list = function () {
        this.disable_list()
        this.clear_list();
        this.assignment_list.clear_list(true);

        var settings = {
            processData : false,
            cache : false,
            type : "GET",
            dataType : "json",
            success : $.proxy(this.handle_load_list, this),
            error : utils.log_ajax_error,
        };
        var url = utils.url_path_join(this.base_url, 'courses');
        ajax(url, settings);
    };

    CourseList.prototype.handle_load_list = function (data, status, xhr) {
        if (data.success) {
            this.load_list_success(data.value);
        } else {
            this.default_course_element.text("Error fetching courses!");
            this.enable_list();
            this.assignment_list.show_error(data.value);
        }
    };

    CourseList.prototype.load_list_success = function (data) {
        this.data = data;
        this.disable_list()
        this.clear_list();

        if (this.data.length === 0) {
            this.default_course_element.text("No courses found.");
            this.assignment_list.clear_list();
            this.enable_list()
            return;
        }

        if ($.inArray(this.current_course, this.data) === -1) {
            this.current_course = undefined;
        }

        if (this.current_course === undefined) {
            this.change_course(this.data[0]);
        } else {
            // we still want to "change" the course here to update the
            // assignment list
            this.change_course(this.current_course);
        }
    };


    CourseList.prototype.change_course = function (course) {
        this.disable_list();
        if (this.current_course !== undefined) {
            this.default_course_element.text(course);
        }
        this.current_course = course;
        this.default_course_element.text(this.current_course);
        var success = $.proxy(this.load_assignment_list_success, this);
        this.assignment_list.load_list(course, success);
    };


    CourseList.prototype.load_assignment_list_success = function () {
        if (this.data) {
            var that = this;
            var set_course = function (course) {
                return function () { that.change_course(course); };
            }

            for (var i=0; i<this.data.length; i++) {
                var element = $('<li/>').append($('<a/>').attr("href", "#").text(this.data[i]));
                element.click(set_course(this.data[i]));
                this.course_list_element.append(element);
            }

            this.data = undefined;
        }

        this.enable_list();
    };

    var AssignmentList = function (released_selector, fetched_selector, submitted_selector, options) {
        this.released_selector = released_selector;
        this.fetched_selector = fetched_selector;
        this.submitted_selector = submitted_selector;

        this.released_element = $(released_selector);
        this.fetched_element = $(fetched_selector);
        this.submitted_element = $(submitted_selector);

        options = options || {};
        this.options = options;
        this.base_url = options.base_url || utils.get_body_data("baseUrl");

        this.callback = undefined;
    };


    AssignmentList.prototype.load_list = function (course, callback) {
        this.callback = callback;
        this.clear_list(true);
        var settings = {
            cache : false,
            type : "GET",
            dataType : "json",
            data : {
                course_id: course
            },
            success : $.proxy(this.handle_load_list, this),
            error : utils.log_ajax_error,
        };
        var url = utils.url_path_join(this.base_url, 'assignments');
        ajax(url, settings);
    };

    AssignmentList.prototype.clear_list = function (loading) {
        var elems = [this.released_element, this.fetched_element, this.submitted_element];
        var i;

        // remove list items
        for (i = 0; i < elems.length; i++) {
            elems[i].children('.list_item').remove();
            if (loading) {
                // show loading
                elems[i].children('.list_loading').show();
                // hide placeholders and errors
                elems[i].children('.list_placeholder').hide();
                elems[i].children('.list_error').hide();

            } else {
                // show placeholders
                elems[i].children('.list_placeholder').show();
                // hide loading and errors
                elems[i].children('.list_loading').hide();
                elems[i].children('.list_error').hide();
            }
        }
    };

    AssignmentList.prototype.show_error = function (error) {
        var elems = [this.released_element, this.fetched_element, this.submitted_element];
        var i;

        // remove list items
        for (i = 0; i < elems.length; i++) {
            elems[i].children('.list_item').remove();
            // show errors
            elems[i].children('.list_error').show();
            elems[i].children('.list_error').text(error);
            // hide loading and placeholding
            elems[i].children('.list_loading').hide();
            elems[i].children('.list_placeholder').hide();
        }
    };

    AssignmentList.prototype.handle_load_list = function (data, status, xhr) {
        if (data.success) {
            this.load_list_success(data.value);
        } else {
            this.show_error(data.value);
        }
    };

    AssignmentList.prototype.load_list_success = function (data) {
        this.clear_list();
        var len = data.length;
        for (var i=0; i<len; i++) {
            var element = $('<div/>');
            var item = new Assignment(element, data[i], this.fetched_selector, $.proxy(this.handle_load_list, this), this.options);
            if (data[i]['status'] === 'released') {
                this.released_element.append(element);
                this.released_element.children('.list_placeholder').hide();
            } else if (data[i]['status'] === 'fetched') {
                this.fetched_element.append(element);
                this.fetched_element.children('.list_placeholder').hide();
            } else if (data[i]['status'] === 'submitted') {
                this.submitted_element.append(element);
                this.submitted_element.children('.list_placeholder').hide();
            }
        }

        // Add collapse arrows.
        $('.assignment-notebooks-link').each(function(index, el) {
            var $link = $(el);
            var $icon = $('<i />')
                .addClass('fa fa-caret-down')
                .css('transform', 'rotate(-90deg)')
                .css('borderSpacing', '90')
                .css('margin-left', '3px');
            $link.append($icon);
            $link.down = false;
            $link.click(function () {
                if ($link.down) {
                    $link.down = false;
                    // jQeury doesn't know how to animate rotations.  Abuse
                    // jQueries animate function by using an unused css attribute
                    // to do the animation (borderSpacing).
                    $icon.animate({ borderSpacing: 90 }, {
                        step: function(now,fx) {
                            $icon.css('transform','rotate(-' + now + 'deg)');
                        }
                    }, 250);
                } else {
                    $link.down = true;
                    // See comment above.
                    $icon.animate({ borderSpacing: 0 }, {
                        step: function(now,fx) {
                            $icon.css('transform','rotate(-' + now + 'deg)');
                        }
                    }, 250);
                }
            });
        });

        if (this.callback) {
            this.callback();
            this.callback = undefined;
        }
    };


    var Assignment = function (element, data, parent, on_refresh, options) {
        this.element = $(element);
        this.data = data;
        this.parent = parent;
        this.on_refresh = on_refresh;
        this.options = options;
        this.base_url = options.base_url || utils.get_body_data("baseUrl");
        this.style();
        this.make_row();
    };

    Assignment.prototype.style = function () {
        this.element.addClass('list_item').addClass("row");
    };

    Assignment.prototype.escape_id = function () {
        // construct the id from the course id and the assignment id, and also
        // prepend the id with "nbgrader" (this also ensures that the first
        // character is always a letter, as required by HTML 4)
        var id = "nbgrader-" + this.data.course_id + "-" + this.data.assignment_id;

        // replace spaces with '_'
        id = id.replace(/ /g, "_");

        // remove any characters that are invalid in HTML div ids
        id = id.replace(/[^A-Za-z0-9\-_]/g, "");

        return id;
    };

    Assignment.prototype.make_row = function () {
        var row = $('<div/>').addClass('col-md-12');
        row.append(this.make_link());
        row.append($('<span/>').addClass('item_course col-sm-2').text(this.data.course_id));
        if (this.data.status === 'submitted') {
            row.append($('<span/>').addClass('item_status col-sm-4').text(this.data.timestamp));
        } else {
            row.append(this.make_button());
        }
        this.element.empty().append(row);

        if (this.data.status === 'fetched') {
            var id = this.escape_id();
            var children = $('<div/>')
                .attr("id", id)
                .addClass("panel-collapse collapse list_container assignment-notebooks")
                .attr("role", "tabpanel");

            var element, child;
            children.append($('<div/>').addClass('list_item row'));
            for (var i=0; i<this.data.notebooks.length; i++) {
                element = $('<div/>');
                this.data.notebooks[i].course_id = this.data.course_id;
                this.data.notebooks[i].assignment_id = this.data.assignment_id;
                child = new Notebook(element, this.data.notebooks[i], this.options);
                children.append(element);
            }

            this.element.append(children);
        }
    };

    Assignment.prototype.make_link = function () {
        var container = $('<span/>').addClass('item_name col-sm-6');
        var link;

        if (this.data.status === 'fetched') {
            var id = this.escape_id();
            link = $('<a/>')
                .addClass("collapsed assignment-notebooks-link")
                .attr("role", "button")
                .attr("data-toggle", "collapse")
                .attr("data-parent", this.parent)
                .attr("href", "#" + id)
                .attr("aria-expanded", "false")
                .attr("aria-controls", id)
        } else {
            link = $('<span/>');
        }

        link.text(this.data.assignment_id);
        container.append(link);
        return container;
    };

    Assignment.prototype.submit_error = function (data) {
        var body = $('<div/>').attr('id', 'submission-message');

        body.append(
            $('<div/>').append(
                $('<p/>').text('Assignment not submitted:')
            )
        );
        body.append(
            $('<pre/>').text(data.value)
        );

        dialog.modal({
            title: "Invalid Submission",
            body: body,
            buttons: { OK: { class : "btn-primary" } }
        });
    };

    Assignment.prototype.make_button = function () {
        var that = this;
        var container = $('<span/>').addClass('item_status col-sm-4');
        var button = $('<button/>').addClass("btn btn-primary btn-xs");
        container.append(button);

        if (this.data.status == 'released') {
            button.text("Fetch");
            button.click(function (e) {
                var settings = {
                    cache : false,
                    data : {
                        course_id: that.data.course_id,
                        assignment_id: that.data.assignment_id
                    },
                    type : "POST",
                    dataType : "json",
                    success : $.proxy(that.on_refresh, that),
                    error : function (xhr, status, error) {
                        container.empty().text("Error fetching assignment.");
                        utils.log_ajax_error(xhr, status, error);
                    }
                };
                button.text('Fetching...');
                button.attr('disabled', 'disabled');
                var url = utils.url_path_join(
                    that.base_url,
                    'assignments',
                    'fetch'
                );
                ajax(url, settings);
            });

        } else if (this.data.status == 'fetched') {
            button.text("Submit");
            button.click(function (e) {
                var settings = {
                    cache : false,
                    data : {
                        course_id: that.data.course_id,
                        assignment_id: that.data.assignment_id
                    },
                    type : "POST",
                    dataType : "json",
                    success : function (data, status, xhr) {
                        if (!data.success) {
                            that.submit_error(data);
                            button.text('Submit');
                            button.removeAttr('disabled');
                        } else {
                            that.on_refresh(data, status, xhr);
                        }
                    },
                    error : function (xhr, status, error) {
                        container.empty().text("Error submitting assignment.");
                        utils.log_ajax_error(xhr, status, error);
                    }
                };
                button.text('Submitting...');
                button.attr('disabled', 'disabled');
                var url = utils.url_path_join(
                    that.base_url,
                    'assignments',
                    'submit'
                );
                ajax(url, settings);
            });
        }

        return container;
    };

    var Notebook = function (element, data, options) {
        this.element = $(element);
        this.data = data;
        this.options = options;
        this.base_url = options.base_url || utils.get_body_data("baseUrl");
        this.style();
        this.make_row();
    };

    Notebook.prototype.style = function () {
        this.element.addClass('list_item').addClass("row");
    };

    Notebook.prototype.make_row = function () {
        var container = $('<div/>').addClass('col-md-12');
        var url = utils.url_path_join(this.base_url, 'tree', utils.url_join_encode(this.data.path));
        var link = $('<span/>').addClass('item_name col-sm-6').append(
            $('<a/>')
                .attr("href", url)
                .attr("target", "_blank")
                .text(this.data.notebook_id));
        container.append(link);
        container.append($('<span/>').addClass('item_course col-sm-2'));
        container.append(this.make_button());
        this.element.append(container);
    };

    Notebook.prototype.make_button = function () {
        var that = this;
        var container = $('<span/>').addClass('item_status col-sm-4');
        var button = $('<button/>').addClass("btn btn-default btn-xs");
        container.append(button);

        button.text("Validate");
        button.click(function (e) {
            var settings = {
                cache : false,
                data : { path: that.data.path },
                type : "POST",
                dataType : "json",
                success : function (data, status, xhr) {
                    button.text('Validate');
                    button.removeAttr('disabled');
                    that.validate(data, button);
                },
                error : function (xhr, status, error) {
                    container.empty().text("Error validating assignment.");
                    utils.log_ajax_error(xhr, status, error);
                }
            };
            button.text('Validating...');
            button.attr('disabled', 'disabled');
            var url = utils.url_path_join(
                that.base_url,
                'assignments',
                'validate'
            );
            ajax(url, settings);
        });

        return container;
    };

    Notebook.prototype.validate_success = function (button) {
        button
            .removeClass("btn-default")
            .removeClass("btn-danger")
            .removeClass("btn-success")
            .addClass("btn-success");
    };

    Notebook.prototype.validate_failure = function (button) {
        button
            .removeClass("btn-default")
            .removeClass("btn-danger")
            .removeClass("btn-success")
            .addClass("btn-danger");
    };

    Notebook.prototype.validate = function (data, button) {
        var body = $('<div/>').attr("id", "validation-message");
        if (data.success) {
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
                this.validate_failure(button);

            } else if (data.passed !== undefined) {
                for (var i=0; i<data.changed.length; i++) {
                    body.append($('<div/>').append($('<p/>').text('The following cell passed:')));
                    body.append($('<pre/>').text(data.passed[i].source));
                }
                body.addClass("validation-passed");
                this.validate_failure(button);

            } else if (data.failed !== undefined) {
                for (var i=0; i<data.failed.length; i++) {
                    body.append($('<div/>').append($('<p/>').text('The following cell failed:')));
                    body.append($('<pre/>').text(data.failed[i].source));
                    body.append($('<pre/>').html(data.failed[i].error));
                }
                body.addClass("validation-failed");
                this.validate_failure(button);

            } else {
                body.append($('<div/>').append($('<p/>').text('Success! Your notebook passes all the tests.')));
                body.addClass("validation-success");
                this.validate_success(button);
            }

        } else {
            body.append($('<div/>').append($('<p/>').text('There was an error running the validate command:')));
            body.append($('<pre/>').text(data.value));
            this.validate_failure(button);
        }

        dialog.modal({
            title: "Validation Results",
            body: body,
            buttons: { OK: { class : "btn-primary" } }
        });
    };

    return {
        'CourseList': CourseList,
        'AssignmentList': AssignmentList,
        'Assignment': Assignment,
        'Notebook': Notebook
    };
});
