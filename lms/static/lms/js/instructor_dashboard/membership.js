/**
 * Membership Section
 */
(function(Mustache, Slick, NotificationModel, NotificationView) {
    'use strict';

    var AuthList, AuthListWidget, BatchEnrollment, BetaTesterBulkAddition, MemberListWidget,
        Membership, emailStudents, plantTimeout, std_ajax_err,
        __hasProp = {}.hasOwnProperty,
        __extends = function(child, parent) {
            var key;
            for (key in parent) {
                if (__hasProp.call(parent, key)) {
                    child[key] = parent[key];
                }
            }
            function Ctor() {
                this.constructor = child;
            }
            Ctor.prototype = parent.prototype;
            child.prototype = new Ctor();
            child.__super__ = parent.prototype;
            return child;
        };

    plantTimeout = function() {
        return window.InstructorDashboard.util.plantTimeout.apply(this, arguments);
    };

    std_ajax_err = function() {
        return window.InstructorDashboard.util.std_ajax_err.apply(this, arguments);
    };

    emailStudents = false;

    MemberListWidget = (function() {

        function MemberListWidget($container, params) {
            var template_html,
                _this = this;
            this.$container = $container;
            if (params === null) {
                params = {};
            }
            params = _.defaults(params, {
                title: 'Member List',
                info: 'Use this list to manage members.',
                labels: ['field1', 'field2', 'field3'],
                add_placeholder: 'Enter name',
                add_btn_label: 'Add Member',
                add_handler: function() {}
            });
            template_html = $('#member-list-widget-template').html();
            this.$container.html(Mustache.render(template_html, params));
            this.$('input[type="button"].add').click(function() {
                if (typeof params.add_handler === 'function') {
                    params.add_handler(_this.$('.add-field').val());
                }
            });
        }

        MemberListWidget.prototype.clear_input = function() {
            return this.$('.add-field').val('');
        };

        MemberListWidget.prototype.clear_rows = function() {
            return this.$('table tbody').empty();
        };

        MemberListWidget.prototype.add_row = function(row_array) {
            var $tbody, $td, $tr, item, _i, _len;
            $tbody = this.$('table tbody');
            $tr = $('<tr>');
            for (_i = 0, _len = row_array.length; _i < _len; _i++) {
                item = row_array[_i];
                $td = $('<td>');
                if (item instanceof jQuery) {
                    $td.append(item);
                } else {
                    $td.text(item);
                }
                $tr.append($td);
            }
            return $tbody.append($tr);
        };

        MemberListWidget.prototype.$ = function(selector) {
            var s;
            if (this.debug !== null) {
                s = this.$container.find(selector);
                if ((s !== null ? s.length : void 0) !== 1) {
                    console.warn('local selector "' + selector + '" found (' + s.length + ') results');
                }
                return s;
            } else {
                return this.$container.find(selector);
            }
        };

        return MemberListWidget;

    })();

    AuthListWidget = (function(_super) {

        __extends(AuthListWidget, _super);

        function AuthListWidget($container, rolename, $error_section) {
            var _this = this;
            this.rolename = rolename;
            this.$error_section = $error_section;
            AuthListWidget.__super__.constructor.call(this, $container, {
                title: $container.data('display-name'),
                info: $container.data('info-text'),
                labels: [gettext('Username'), gettext('Email'), gettext('Revoke access')],
                add_placeholder: gettext('Enter username or email'),
                add_btn_label: $container.data('add-button-label'),
                add_handler: function(input) {
                    return _this.add_handler(input);
                }
            });
            this.debug = true;
            this.list_endpoint = $container.data('list-endpoint');
            this.modify_endpoint = $container.data('modify-endpoint');
            if (this.rolename === null) {
                throw 'AuthListWidget missing @rolename';
            }
            this.reload_list();
        }

        AuthListWidget.prototype.re_view = function() {
            this.clear_errors();
            this.clear_input();
            return this.reload_list();
        };

        AuthListWidget.prototype.add_handler = function(input) {
            var _this = this;
            if ((input !== null) && input !== '') {
                return this.modify_member_access(input, 'allow', function(error) {
                    if (error !== null) {
                        return _this.show_errors(error);
                    }
                    _this.clear_errors();
                    _this.clear_input();
                    return _this.reload_list();
                });
            } else {
                return this.show_errors(gettext('Please enter a username or email.'));
            }
        };

        AuthListWidget.prototype.reload_list = function() {
            var _this = this;
            return this.get_member_list(function(error, member_list) {
                if (error !== null) {
                    return _this.show_errors(error);
                }
                _this.clear_rows();
                return _.each(member_list, function(member) {
                    var $revoke_btn, label_trans;
                    label_trans = gettext('Revoke access');
                    $revoke_btn = $(
                        edx.HtmlUtils.joinHtml(
                            edx.HtmlUtils.HTML(
                                '<div class="revoke"><span class="icon fa fa-times-circle" aria-hidden="true"></span>'
                            ),
                            label_trans,
                            edx.HtmlUtils.HTML('</div>')
                        ).toString()
                    );
                    $revoke_btn.click(function() {
                        return _this.modify_member_access(member.email, 'revoke', function(error) {
                            if (error !== null) {
                                return _this.show_errors(error);
                            }
                            _this.clear_errors();
                            return _this.reload_list();
                        });
                    });
                    return _this.add_row([member.username, member.email, $revoke_btn]);
                });
            });
        };

        AuthListWidget.prototype.clear_errors = function() {
            var _ref;
            return (_ref = this.$error_section) !== null ? _ref.text('') : void 0;
        };

        AuthListWidget.prototype.show_errors = function(msg) {
            var _ref;
            return (_ref = this.$error_section) !== null ? _ref.text(msg) : void 0;
        };

        AuthListWidget.prototype.get_member_list = function(cb) {
            var _this = this;
            return $.ajax({
                type: 'POST',
                dataType: 'json',
                url: this.list_endpoint,
                data: {
                    rolename: this.rolename
                },
                success: function(data) {
                    return typeof cb === 'function' ? cb(null, data[_this.rolename]) : void 0;
                },
                error: std_ajax_err(function() {
                    if (typeof cb === 'function') {
                        cb(edx.StringUtils.interpolate(
                            // Translators: the role name is something like "staff" or "beta tester".
                            gettext('Error fetching list for role "{role_name}"'),
                            {role_name: this.rolename}
                        ));
                    }
                })
            });
        };

        AuthListWidget.prototype.modify_member_access = function(unique_student_identifier, action, cb) {
            var _this = this;
            return $.ajax({
                type: 'POST',
                dataType: 'json',
                url: this.modify_endpoint,
                data: {
                    unique_student_identifier: unique_student_identifier,
                    rolename: this.rolename,
                    action: action
                },
                success: function(data) {
                    return _this.member_response(data);
                },
                error: std_ajax_err(function() {
                    if (typeof cb === 'function') {
                        cb(gettext("Error changing user's permissions."));
                    }
                })
            });
        };

        AuthListWidget.prototype.member_response = function(data) {
            var msg;
            this.clear_errors();
            this.clear_input();
            if (data.userDoesNotExist) {
                msg = gettext('Could not find a user with username or email address {identifier}.');
                return this.show_errors(edx.StringUtils.interpolate(msg, {
                    identifier: data.unique_student_identifier
                }));
            } else if (data.inactiveUser) {
                msg = gettext('Error: User {username} has not yet activated their account. Users must create and activate their accounts before they can be assigned a role.');  // jshint ignore:line
                return this.show_errors(edx.StringUtils.interpolate(msg, {
                    username: data.unique_student_identifier
                }));
            } else if (data.removingSelfAsInstructor) {
                return this.show_errors(gettext('Error: You cannot remove yourself from the Instructor group!'));
            } else {
                return this.reload_list();
            }
        };

        return AuthListWidget;

    })(MemberListWidget);

    this.AutoEnrollmentViaCsv = (function() {

        function AutoEnrollmentViaCsv($container) {
            var _this = this;
            this.$container = $container;
            this.$student_enrollment_form = this.$container.find('form#student-auto-enroll-form');
            this.$enrollment_signup_button = this.$container.find('name="enrollment_signup_button"]');
            this.$students_list_file = this.$container.find('input[name="students_list"]');
            this.$csrf_token = this.$container.find('input[name="csrfmiddlewaretoken"]');
            this.$results = this.$container.find('div.results');
            this.$browse_button = this.$container.find('#browseBtn');
            this.$browse_file = this.$container.find('#browseFile');
            this.processing = false;
            this.$browse_button.on('change', function(event) {
                if (event.currentTarget.files.length === 1) {
                    return _this.$browse_file.val(event.currentTarget.value.substring(event.currentTarget.value.lastIndexOf('\\') + 1));
                }
            });
            this.$enrollment_signup_button.click(function() {
                return _this.$student_enrollment_form.submit(function(event) {
                    var data;
                    if (_this.processing) {
                        return false;
                    }
                    _this.processing = true;
                    event.preventDefault();
                    data = new FormData(event.currentTarget);
                    $.ajax({
                        dataType: 'json',
                        type: 'POST',
                        url: event.currentTarget.action,
                        data: data,
                        processData: false,
                        contentType: false,
                        success: function(data) {
                            _this.processing = false;
                            return _this.display_response(data);
                        }
                    });
                    return false;
                });
            });
        }

        AutoEnrollmentViaCsv.prototype.display_response = function(dataFromServer) {
            var error, errors, general_error, render_response, result_from_server_is_success, warning, warnings,
                _i, _j, _k, _len, _len1, _len2, _ref, _ref1, _ref2,
                _this = this;
            this.$results.empty();
            errors = [];
            warnings = [];
            result_from_server_is_success = true;
            if (dataFromServer.general_errors.length) {
                result_from_server_is_success = false;
                _ref = dataFromServer.general_errors;
                for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                    general_error = _ref[_i];
                    general_error.is_general_error = true;
                    errors.push(general_error);
                }
            }
            if (dataFromServer.row_errors.length) {
                result_from_server_is_success = false;
                _ref1 = dataFromServer.row_errors;
                for (_j = 0, _len1 = _ref1.length; _j < _len1; _j++) {
                    error = _ref1[_j];
                    error.is_general_error = false;
                    errors.push(error);
                }
            }
            if (dataFromServer.warnings.length) {
                result_from_server_is_success = false;
                _ref2 = dataFromServer.warnings;
                for (_k = 0, _len2 = _ref2.length; _k < _len2; _k++) {
                    warning = _ref2[_k];
                    warning.is_general_error = false;
                    warnings.push(warning);
                }
            }
            render_response = function(title, message, type, studentResults) {
                var details, response_message, student_result, _l, _len3;
                details = [];
                for (_l = 0, _len3 = studentResults.length; _l < _len3; _l++) {
                    student_result = studentResults[_l];
                    if (student_result.is_general_error) {
                        details.push(student_result.response);
                    } else {
                        response_message = student_result.username + '  (' + student_result.email + '):  ' +
                            '   (' + student_result.response + ')';
                        details.push(response_message);
                    }
                }
                return _this.$results.append(_this.render_notification_view(type, title, message, details));
            };
            if (errors.length) {
                render_response(
                    gettext('Errors'), gettext('The following errors were generated:'), 'error', errors
                );
            }
            if (warnings.length) {
                render_response(
                    gettext('Warnings'), gettext('The following warnings were generated:'), 'warning', warnings
                );
            }
            if (result_from_server_is_success) {
                return render_response(
                    gettext('Success'), gettext('All accounts were created successfully.'), 'confirmation', []
                );
            }
        };

        AutoEnrollmentViaCsv.prototype.render_notification_view = function(type, title, message, details) {
            var notification_model, view;
            notification_model = new NotificationModel();
            notification_model.set({
                'type': type,
                'title': title,
                'message': message,
                'details': details
            });
            view = new NotificationView({
                model: notification_model
            });
            view.render();
            return view.$el.html();
        };

        return AutoEnrollmentViaCsv;

    })();

    BetaTesterBulkAddition = (function() {

        function BetaTesterBulkAddition($container) {
            var _this = this;
            this.$container = $container;
            this.$identifier_input = this.$container.find('extarea[name="student-ids-for-beta"]');
            this.$btn_beta_testers = this.$container.find('input[name="beta-testers"]');
            this.$checkbox_autoenroll = this.$container.find('input[name="auto-enroll"]');
            this.$checkbox_emailstudents = this.$container.find('input[name="email-students-beta"]');
            this.$task_response = this.$container.find('.request-response');
            this.$request_response_error = this.$container.find('.request-response-error');
            this.$btn_beta_testers.click(function(event) {
                var autoEnroll, send_data;
                emailStudents = _this.$checkbox_emailstudents.is(':checked');
                autoEnroll = _this.$checkbox_autoenroll.is(':checked');
                send_data = {
                    action: $(event.target).data('action'),
                    identifiers: _this.$identifier_input.val(),
                    email_students: emailStudents,
                    auto_enroll: autoEnroll
                };
                return $.ajax({
                    dataType: 'json',
                    type: 'POST',
                    url: _this.$btn_beta_testers.data('endpoint'),
                    data: send_data,
                    success: function(data) {
                        return _this.display_response(data);
                    },
                    error: std_ajax_err(function() {
                        return _this.fail_with_error(gettext('Error adding/removing users as beta testers.'));
                    })
                });
            });
        }

        BetaTesterBulkAddition.prototype.clear_input = function() {
            this.$identifier_input.val('');
            this.$checkbox_emailstudents.attr('checked', true);
            return this.$checkbox_autoenroll.attr('checked', true);
        };

        BetaTesterBulkAddition.prototype.fail_with_error = function(msg) {
            console.warn(msg);
            this.clear_input();
            this.$task_response.empty();
            this.$request_response_error.empty();
            return this.$request_response_error.text(msg);
        };

        BetaTesterBulkAddition.prototype.display_response = function(data_from_server) {
            var errors, no_users, render_list, sr, student_results, successes, _i, _len, _ref,
                _this = this;
            this.clear_input();
            this.$task_response.empty();
            this.$request_response_error.empty();
            errors = [];
            successes = [];
            no_users = [];
            _ref = data_from_server.results;
            for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                student_results = _ref[_i];
                if (student_results.userDoesNotExist) {
                    no_users.push(student_results);
                } else if (student_results.error) {
                    errors.push(student_results);
                } else {
                    successes.push(student_results);
                }
            }
            render_list = function(label, ids) {
                var identifier, ids_list, task_res_section, _j, _len1;
                task_res_section = $('<div/>', {
                    'class': 'request-res-section'
                });
                task_res_section.append($('<h3/>', {
                    text: label
                }));
                ids_list = $('<ul/>');
                task_res_section.append(ids_list);
                for (_j = 0, _len1 = ids.length; _j < _len1; _j++) {
                    identifier = ids[_j];
                    ids_list.append($('<li/>', {
                        text: identifier
                    }));
                }
                return _this.$task_response.append(task_res_section);
            };
            if (successes.length && data_from_server.action === 'add') {
                // Translators: A list of users appears after this sentence;
                render_list(gettext('These users were successfully added as beta testers:'), (function() {
                    var _j, _len1, _results;
                    _results = [];
                    for (_j = 0, _len1 = successes.length; _j < _len1; _j++) {
                        sr = successes[_j];
                        _results.push(sr.identifier);
                    }
                    return _results;
                })());
            }
            if (successes.length && data_from_server.action === 'remove') {
                // Translators: A list of users appears after this sentence;
                render_list(gettext('These users were successfully removed as beta testers:'), (function() {
                    var _j, _len1, _results;
                    _results = [];
                    for (_j = 0, _len1 = successes.length; _j < _len1; _j++) {
                        sr = successes[_j];
                        _results.push(sr.identifier);
                    }
                    return _results;
                })());
            }
            if (errors.length && data_from_server.action === 'add') {
                // Translators: A list of users appears after this sentence;
                render_list(gettext('These users were not added as beta testers:'), (function() {
                    var _j, _len1, _results;
                    _results = [];
                    for (_j = 0, _len1 = errors.length; _j < _len1; _j++) {
                        sr = errors[_j];
                        _results.push(sr.identifier);
                    }
                    return _results;
                })());
            }
            if (errors.length && data_from_server.action === 'remove') {
                // Translators: A list of users appears after this sentence;
                render_list(gettext('These users were not removed as beta testers:'), (function() {
                    var _j, _len1, _results;
                    _results = [];
                    for (_j = 0, _len1 = errors.length; _j < _len1; _j++) {
                        sr = errors[_j];
                        _results.push(sr.identifier);
                    }
                    return _results;
                })());
            }
            if (no_users.length) {
                no_users.push($(gettext('Users must create and activate their account before they can be promoted to beta tester.')));  // jshint ignore:line
                return render_list(
                    // Translators: A list of identifiers (which are email addresses and/or usernames)
                    // appears after this sentence.
                    gettext('Could not find users associated with the following identifiers:'),
                    (function() {
                        var _j, _len1, _results;
                        _results = [];
                        for (_j = 0, _len1 = no_users.length; _j < _len1; _j++) {
                            sr = no_users[_j];
                            _results.push(sr.identifier);
                        }
                        return _results;
                    })()
                );
            }
        };

        return BetaTesterBulkAddition;

    })();

    BatchEnrollment = (function() {

        function BatchEnrollment($container) {
            var _this = this;
            this.$container = $container;
            this.$identifier_input = this.$container.find('textarea[name="student-ids"]');
            this.$enrollment_button = this.$container.find('.enrollment-button');
            this.$is_course_white_label = this.$container.find('#is_course_white_label').val();
            this.$reason_field = this.$container.find('textarea[name="reason-field"]');
            this.$checkbox_autoenroll = this.$container.find('input[name="auto-enroll"]');
            this.$checkbox_emailstudents = this.$container.find('input[name="email-students"]');
            this.$task_response = this.$container.find('.request-response');
            this.$request_response_error = this.$container.find('.request-response-error');
            this.$enrollment_button.click(function(event) {
                var send_data;
                if (_this.$is_course_white_label === 'True') {
                    if (!_this.$reason_field.val()) {
                        _this.fail_with_error(gettext('Reason field should not be left blank.'));
                        return false;
                    }
                }
                emailStudents = _this.$checkbox_emailstudents.is(':checked');
                send_data = {
                    action: $(event.target).data('action'),
                    identifiers: _this.$identifier_input.val(),
                    auto_enroll: _this.$checkbox_autoenroll.is(':checked'),
                    email_students: emailStudents,
                    reason: _this.$reason_field.val()
                };
                return $.ajax({
                    dataType: 'json',
                    type: 'POST',
                    url: $(event.target).data('endpoint'),
                    data: send_data,
                    success: function(data) {
                        return _this.display_response(data);
                    },
                    error: std_ajax_err(function() {
                        return _this.fail_with_error(gettext('Error enrolling/unenrolling users.'));
                    })
                });
            });
        }

        BatchEnrollment.prototype.clear_input = function() {
            this.$identifier_input.val('');
            this.$reason_field.val('');
            this.$checkbox_emailstudents.attr('checked', true);
            return this.$checkbox_autoenroll.attr('checked', true);
        };

        BatchEnrollment.prototype.fail_with_error = function(msg) {
            console.warn(msg);
            this.clear_input();
            this.$task_response.empty();
            this.$request_response_error.empty();
            return this.$request_response_error.text(msg);
        };

        BatchEnrollment.prototype.display_response = function(dataFromServer) {
            var allowed, autoenrolled, enrolled, errors, errors_label, invalid_identifier,
                notenrolled, notunenrolled, render_list, sr, student_results, _i, _j, _len, _len1, _ref,
                _this = this;
            this.clear_input();
            this.$task_response.empty();
            this.$request_response_error.empty();
            invalid_identifier = [];
            errors = [];
            enrolled = [];
            allowed = [];
            autoenrolled = [];
            notenrolled = [];
            notunenrolled = [];
            _ref = dataFromServer.results;
            for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                student_results = _ref[_i];
                if (student_results.invalidIdentifier) {
                    invalid_identifier.push(student_results);
                } else if (student_results.error) {
                    errors.push(student_results);
                } else if (student_results.after.enrollment) {
                    enrolled.push(student_results);
                } else if (student_results.after.allowed) {
                    if (student_results.after.auto_enroll) {
                        autoenrolled.push(student_results);
                    } else {
                        allowed.push(student_results);
                    }
                } else if (dataFromServer.action === 'unenroll' &&
                    !student_results.before.enrollment &&
                    !student_results.before.allowed) {
                    notunenrolled.push(student_results);
                } else if (!student_results.after.enrollment) {
                    notenrolled.push(student_results);
                } else {
                    console.warn('student results not reported to user');
                    console.warn(student_results);
                }
            }
            render_list = function(label, ids) {
                var identifier, ids_list, task_res_section, _j, _len1;
                task_res_section = $('<div/>', {
                    'class': 'request-res-section'
                });
                task_res_section.append($('<h3/>', {
                    text: label
                }));
                ids_list = $('<ul/>');
                task_res_section.append(ids_list);
                for (_j = 0, _len1 = ids.length; _j < _len1; _j++) {
                    identifier = ids[_j];
                    ids_list.append($('<li/>', {
                        text: identifier
                    }));
                }
                return _this.$task_response.append(task_res_section);
            };
            if (invalid_identifier.length) {
                render_list(gettext('The following email addresses and/or usernames are invalid:'), (function() {
                    var _j, _len1, _results;
                    _results = [];
                    for (_j = 0, _len1 = invalid_identifier.length; _j < _len1; _j++) {
                        sr = invalid_identifier[_j];
                        _results.push(sr.identifier);
                    }
                    return _results;
                })());
            }
            if (errors.length) {
                errors_label = (function() {
                    if (dataFromServer.action === 'enroll') {
                        return 'There was an error enrolling:';
                    } else if (dataFromServer.action === 'unenroll') {
                        return 'There was an error unenrolling:';
                    } else {
                        console.warn('unknown action from server "' + dataFromServer.action + '"');
                        return 'There was an error processing:';
                    }
                })();
                for (_j = 0, _len1 = errors.length; _j < _len1; _j++) {
                    student_results = errors[_j];
                    render_list(errors_label, (function() {
                        var _k, _len2, _results;
                        _results = [];
                        for (_k = 0, _len2 = errors.length; _k < _len2; _k++) {
                            sr = errors[_k];
                            _results.push(sr.identifier);
                        }
                        return _results;
                    })());
                }
            }
            if (enrolled.length && emailStudents) {
                render_list(gettext('Successfully enrolled and sent email to the following users:'), (function() {
                    var _k, _len2, _results;
                    _results = [];
                    for (_k = 0, _len2 = enrolled.length; _k < _len2; _k++) {
                        sr = enrolled[_k];
                        _results.push(sr.identifier);
                    }
                    return _results;
                })());
            }
            if (enrolled.length && !emailStudents) {
                // Translators: A list of users appears after this sentence;
                render_list(gettext('Successfully enrolled the following users:'), (function() {
                    var _k, _len2, _results;
                    _results = [];
                    for (_k = 0, _len2 = enrolled.length; _k < _len2; _k++) {
                        sr = enrolled[_k];
                        _results.push(sr.identifier);
                    }
                    return _results;
                })());
            }
            if (allowed.length && emailStudents) {
                // Translators: A list of users appears after this sentence;
                render_list(
                    gettext('Successfully sent enrollment emails to the following users. They will be allowed to enroll once they register:'),  // jshint ignore:line
                    (function() {
                        var _k, _len2, _results;
                        _results = [];
                        for (_k = 0, _len2 = allowed.length; _k < _len2; _k++) {
                            sr = allowed[_k];
                            _results.push(sr.identifier);
                        }
                        return _results;
                    })()
                );
            }
            if (allowed.length && !emailStudents) {
                // Translators: A list of users appears after this sentence;
                render_list(gettext('These users will be allowed to enroll once they register:'), (function() {
                    var _k, _len2, _results;
                    _results = [];
                    for (_k = 0, _len2 = allowed.length; _k < _len2; _k++) {
                        sr = allowed[_k];
                        _results.push(sr.identifier);
                    }
                    return _results;
                })());
            }
            if (autoenrolled.length && emailStudents) {
                // Translators: A list of users appears after this sentence;
                render_list(
                    gettext('Successfully sent enrollment emails to the following users. They will be enrolled once they register:'),  // jshint ignore:line
                    (function() {
                        var _k, _len2, _results;
                        _results = [];
                        for (_k = 0, _len2 = autoenrolled.length; _k < _len2; _k++) {
                            sr = autoenrolled[_k];
                            _results.push(sr.identifier);
                        }
                        return _results;
                    })()
                );
            }
            if (autoenrolled.length && !emailStudents) {
                // Translators: A list of users appears after this sentence;
                render_list(gettext('These users will be enrolled once they register:'), (function() {
                    var _k, _len2, _results;
                    _results = [];
                    for (_k = 0, _len2 = autoenrolled.length; _k < _len2; _k++) {
                        sr = autoenrolled[_k];
                        _results.push(sr.identifier);
                    }
                    return _results;
                })());
            }
            if (notenrolled.length && emailStudents) {
                // Translators: A list of users appears after this sentence;
                render_list(
                    gettext('Emails successfully sent. The following users are no longer enrolled in the course:'),
                    (function() {
                        var _k, _len2, _results;
                        _results = [];
                        for (_k = 0, _len2 = notenrolled.length; _k < _len2; _k++) {
                            sr = notenrolled[_k];
                            _results.push(sr.identifier);
                        }
                        return _results;
                    })()
                );
            }
            if (notenrolled.length && !emailStudents) {
                // Translators: A list of users appears after this sentence.
                render_list(
                    gettext('The following users are no longer enrolled in the course:'),
                    (function() {
                        var _k, _len2, _results;
                        _results = [];
                        for (_k = 0, _len2 = notenrolled.length; _k < _len2; _k++) {
                            sr = notenrolled[_k];
                            _results.push(sr.identifier);
                        }
                        return _results;
                    })()
                );
            }
            if (notunenrolled.length) {
                // Translators: A list of users appears after this sentence. This situation arises
                // when a staff member tries to unenroll a user who is not currently enrolled in this course.
                return render_list(
                    gettext('These users were not affiliated with the course so could not be unenrolled:'),
                    (function() {
                        var _k, _len2, _results;
                        _results = [];
                        for (_k = 0, _len2 = notunenrolled.length; _k < _len2; _k++) {
                            sr = notunenrolled[_k];
                            _results.push(sr.identifier);
                        }
                        return _results;
                    })()
                );
            }
        };

        return BatchEnrollment;

    })();

    AuthList = (function() {

        function AuthList($container, rolename) {
            var _this = this;
            this.$container = $container;
            this.rolename = rolename;
            this.$display_table = this.$container.find('.auth-list-table');
            this.$request_response_error = this.$container.find('.request-response-error');
            this.$add_section = this.$container.find('.auth-list-add');
            this.$allow_field = this.$add_section.find('input[name="email"]');
            this.$allow_button = this.$add_section.find('input[name="allow"]');
            this.$allow_button.click(function() {
                _this.access_change(_this.$allow_field.val(), 'allow', function() {
                    return _this.reload_auth_list();
                });
                return _this.$allow_field.val('');
            });
            this.reload_auth_list();
        }

        AuthList.prototype.reload_auth_list = function() {
            var load_auth_list,
                _this = this;
            load_auth_list = function(data) {
                var $table_placeholder, WHICH_CELL_IS_REVOKE, columns, grid, options, table_data;
                _this.$request_response_error.empty();
                _this.$display_table.empty();
                options = {
                    enableCellNavigation: true,
                    enableColumnReorder: false,
                    forceFitColumns: true
                };
                WHICH_CELL_IS_REVOKE = 3;
                columns = [
                    {
                        id: 'username',
                        field: 'username',
                        name: 'Username'
                    }, {
                        id: 'email',
                        field: 'email',
                        name: 'Email'
                    }, {
                        id: 'first_name',
                        field: 'first_name',
                        name: 'First Name'
                    }, {
                        id: 'revoke',
                        field: 'revoke',
                        name: 'Revoke',
                        formatter: function() {
                            return '<span class="revoke-link">Revoke Access</span>';
                        }
                    }
                ];
                table_data = data[_this.rolename];
                $table_placeholder = $('<div/>', {
                    'class': 'slickgrid'
                });
                _this.$display_table.append($table_placeholder);
                grid = new Slick.Grid($table_placeholder, table_data, columns, options);
                return grid.onClick.subscribe(function(e, args) {
                    var item;
                    item = args.grid.getDataItem(args.row);
                    if (args.cell === WHICH_CELL_IS_REVOKE) {
                        return _this.access_change(item.email, 'revoke', function() {
                            return _this.reload_auth_list();
                        });
                    }
                });
            };
            return $.ajax({
                dataType: 'json',
                type: 'POST',
                url: this.$display_table.data('endpoint'),
                data: {
                    rolename: this.rolename
                },
                success: load_auth_list,
                error: std_ajax_err(function() {
                    return _this.$request_response_error.text('Error fetching list for "' + _this.rolename + '"');
                })
            });
        };

        AuthList.prototype.refresh = function() {
            this.$display_table.empty();
            return this.reload_auth_list();
        };

        AuthList.prototype.access_change = function(email, action, cb) {
            var _this = this;
            return $.ajax({
                dataType: 'json',
                type: 'POST',
                url: this.$add_section.data('endpoint'),
                data: {
                    email: email,
                    rolename: this.rolename,
                    action: action
                },
                success: function(data) {
                    return typeof cb === 'function' ? cb(data) : void 0;
                },
                error: std_ajax_err(function() {
                    return _this.$request_response_error.text(gettext("Error changing user's permissions."));
                })
            });
        };

        return AuthList;

    })();

    Membership = (function() {

        function Membership($section) {
            var auth_list, _i, _len, _ref,
                _this = this;
            this.$section = $section;
            this.$section.data('wrapper', this);
            plantTimeout(0, function() {
                return new BatchEnrollment(_this.$section.find('.batch-enrollment'));
            });
            plantTimeout(0, function() {
                return new self.AutoEnrollmentViaCsv(_this.$section.find('.auto_enroll_csv'));
            });
            plantTimeout(0, function() {
                return new BetaTesterBulkAddition(_this.$section.find('.batch-beta-testers'));
            });
            this.$list_selector = this.$section.find('select#member-lists-selector');
            this.$auth_list_containers = this.$section.find('.auth-list-container');
            this.$auth_list_errors = this.$section.find('.member-lists-management .request-response-error');
            this.auth_lists = _.map(this.$auth_list_containers, function(auth_list_container) {
                var rolename;
                rolename = $(auth_list_container).data('rolename');
                return new AuthListWidget($(auth_list_container), rolename, _this.$auth_list_errors);
            });
            this.$list_selector.empty();
            _ref = this.auth_lists;
            for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                auth_list = _ref[_i];
                this.$list_selector.append($('<option/>', {
                    text: auth_list.$container.data('display-name'),
                    data: {
                        auth_list: auth_list
                    }
                }));
            }
            if (this.auth_lists.length === 0) {
                this.$list_selector.hide();
            }
            this.$list_selector.change(function() {
                var $opt, _j, _len1, _ref1;
                $opt = _this.$list_selector.children('option:selected');
                if ($opt.length === 0) {
                    return;
                }
                _ref1 = _this.auth_lists;
                for (_j = 0, _len1 = _ref1.length; _j < _len1; _j++) {
                    auth_list = _ref1[_j];
                    auth_list.$container.removeClass('active');
                }
                auth_list = $opt.data('auth_list');
                auth_list.$container.addClass('active');
                return auth_list.re_view();
            });
            this.$list_selector.change();
        }

        Membership.prototype.onClickTitle = function() {};

        return Membership;

    })();

    _.defaults(window, {
        InstructorDashboard: {}
    });

    _.defaults(window.InstructorDashboard, {
        sections: {}
    });

    _.defaults(window.InstructorDashboard.sections, {
        Membership: Membership
    });

}).call(this, Mustache, Slick, NotificationModel, NotificationView);  // jshint ignore:line
