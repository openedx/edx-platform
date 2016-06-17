/**
 * Student Admin Section
 */
(function() {
    'use strict';

    var PendingInstructorTasks, create_task_list_table, find_and_assert, std_ajax_err;

    std_ajax_err = function() {
        return window.InstructorDashboard.util.std_ajax_err.apply(this, arguments);
    };

    create_task_list_table = function() {
        return window.InstructorDashboard.util.create_task_list_table.apply(this, arguments);
    };

    PendingInstructorTasks = function() {
        return window.InstructorDashboard.util.PendingInstructorTasks;
    };

    find_and_assert = function($root, selector) {
        var item;
        item = $root.find(selector);
        if (item.length !== 1) {
            console.error('element selection failed for "' + selector + '" resulted in length ' + item.length);
            throw 'Failed Element Selection';
        } else {
            return item;
        }
    };

    this.StudentAdmin = (function() {

        function StudentAdmin($section) {
            var _this = this;
            this.$section = $section;
            this.$section.data('wrapper', this);
            this.$field_student_select_progress = find_and_assert(this.$section, 'input[name="student-select-progress"]');  // jshint ignore:line
            this.$field_student_select_grade = find_and_assert(this.$section, 'input[name="student-select-grade"]');
            this.$progress_link = find_and_assert(this.$section, 'a.progress-link');
            this.$field_problem_select_single = find_and_assert(this.$section, 'input[name="problem-select-single"]');
            this.$btn_reset_attempts_single = find_and_assert(this.$section, 'input[name="reset-attempts-single"]');
            this.$btn_delete_state_single = this.$section.find('input[name="delete-state-single"]');
            this.$btn_rescore_problem_single = this.$section.find('input[name="rescore-problem-single"]');
            this.$btn_task_history_single = this.$section.find('input[name="task-history-single"]');
            this.$table_task_history_single = this.$section.find('.task-history-single-table');
            this.$field_entrance_exam_student_select_grade = this.$section.find('input[name="entrance-exam-student-select-grade"]');  // jshint ignore:line
            this.$btn_reset_entrance_exam_attempts = this.$section.find('input[name="reset-entrance-exam-attempts"]');
            this.$btn_delete_entrance_exam_state = this.$section.find('input[name="delete-entrance-exam-state"]');
            this.$btn_rescore_entrance_exam = this.$section.find('input[name="rescore-entrance-exam"]');
            this.$btn_skip_entrance_exam = this.$section.find('input[name="skip-entrance-exam"]');
            this.$btn_entrance_exam_task_history = this.$section.find('input[name="entrance-exam-task-history"]');
            this.$table_entrance_exam_task_history = this.$section.find('.entrance-exam-task-history-table');
            this.$field_problem_select_all = this.$section.find('input[name="problem-select-all"]');
            this.$btn_reset_attempts_all = this.$section.find('input[name="reset-attempts-all"]');
            this.$btn_rescore_problem_all = this.$section.find('input[name="rescore-problem-all"]');
            this.$btn_task_history_all = this.$section.find('input[name="task-history-all"]');
            this.$table_task_history_all = this.$section.find('.task-history-all-table');
            this.instructor_tasks = new (PendingInstructorTasks())(this.$section);
            this.$request_response_error_progress = find_and_assert(this.$section, '.student-specific-container .request-response-error');  // jshint ignore:line
            this.$request_response_error_grade = find_and_assert(this.$section, '.student-grade-container .request-response-error');  // jshint ignore:line
            this.$request_response_error_ee = this.$section.find('.entrance-exam-grade-container .request-response-error');  // jshint ignore:line
            this.$request_response_error_all = this.$section.find('.course-specific-container .request-response-error');  // jshint ignore:line
            this.$progress_link.click(function(e) {
                var uniqueStudentIdentifier;
                e.preventDefault();
                uniqueStudentIdentifier = _this.$field_student_select_progress.val();
                if (!uniqueStudentIdentifier) {
                    return _this.$request_response_error_progress.text(
                        gettext('Please enter a student email address or username.')
                    );
                }
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: _this.$progress_link.data('endpoint'),
                    data: {
                        unique_student_identifier: uniqueStudentIdentifier
                    },
                    success: _this.clear_errors_then(function(data) {
                        window.location = data.progress_url;
                    }),
                    error: std_ajax_err(function() {
                        _this.$request_response_error_progress.text(edx.StringUtils.interpolate(
                            gettext('Error getting student progress url for {student_id}. Make sure that the student identifier is spelled correctly.'),  // jshint ignore:line
                            {student_id: uniqueStudentIdentifier}
                        ));
                    })
                });
            });
            this.$btn_reset_attempts_single.click(function() {
                var problemToReset, sendData, uniqueStudentIdentifier;
                uniqueStudentIdentifier = _this.$field_student_select_grade.val();
                problemToReset = _this.$field_problem_select_single.val();
                if (!uniqueStudentIdentifier) {
                    return _this.$request_response_error_grade.text(
                        gettext('Please enter a student email address or username.')
                    );
                }
                if (!problemToReset) {
                    return _this.$request_response_error_grade.text(
                        gettext('Please enter a problem location.')
                    );
                }
                sendData = {
                    unique_student_identifier: uniqueStudentIdentifier,
                    problem_to_reset: problemToReset,
                    delete_module: false
                };
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: _this.$btn_reset_attempts_single.data('endpoint'),
                    data: sendData,
                    success: _this.clear_errors_then(function() {
                        return alert(edx.StringUtils.interpolate(
                            gettext("Success! Problem attempts reset for problem '<%= problem_id %>' and student '<%= student_id %>'."),  // jshint ignore:line
                            {
                                problem_id: problemToReset,
                                student_id: uniqueStudentIdentifier
                            }
                        ));
                    }),
                    error: std_ajax_err(function() {
                        return _this.$request_response_error_grade.text(edx.StringUtils.interpolate(
                            gettext("Error resetting problem attempts for problem '<%= problem_id %>' and student '<%= student_id %>'. Make sure that the problem and student identifiers are complete and correct."),  // jshint ignore:line
                            {
                                problem_id: problemToReset,
                                student_id: uniqueStudentIdentifier
                            }
                        ));
                    })
                });
            });
            this.$btn_delete_state_single.click(function() {
                var confirmMessage, problemToReset, sendData, uniqueStudentIdentifier;
                uniqueStudentIdentifier = _this.$field_student_select_grade.val();
                problemToReset = _this.$field_problem_select_single.val();
                if (!uniqueStudentIdentifier) {
                    return _this.$request_response_error_grade.text(
                        gettext('Please enter a student email address or username.')
                    );
                }
                if (!problemToReset) {
                    return _this.$request_response_error_grade.text(
                        gettext('Please enter a problem location.')
                    );
                }
                confirmMessage = edx.StringUtils.interpolate(
                    gettext("Delete student '<%= student_id %>'s state on problem '<%= problem_id %>'?"),
                    {
                        student_id: uniqueStudentIdentifier,
                        problem_id: problemToReset
                    }
                );
                if (window.confirm(confirmMessage)) {
                    sendData = {
                        unique_student_identifier: uniqueStudentIdentifier,
                        problem_to_reset: problemToReset,
                        delete_module: true
                    };
                    return $.ajax({
                        type: 'POST',
                        dataType: 'json',
                        url: _this.$btn_delete_state_single.data('endpoint'),
                        data: sendData,
                        success: _this.clear_errors_then(function() {
                            return alert(gettext('Module state successfully deleted.'));
                        }),
                        error: std_ajax_err(function() {
                            return _this.$request_response_error_grade.text(edx.StringUtils.interpolate(
                                gettext("Error deleting student '<%= student_id %>'s state on problem '<%= problem_id %>'. Make sure that the problem and student identifiers are complete and correct."),  // jshint ignore:line
                                {
                                    student_id: uniqueStudentIdentifier,
                                    problem_id: problemToReset
                                }
                            ));
                        })
                    });
                } else {
                    return _this.clear_errors();
                }
            });
            this.$btn_rescore_problem_single.click(function() {
                var problemToReset, sendData, uniqueStudentIdentifier;
                uniqueStudentIdentifier = _this.$field_student_select_grade.val();
                problemToReset = _this.$field_problem_select_single.val();
                if (!uniqueStudentIdentifier) {
                    return _this.$request_response_error_grade.text(
                        gettext('Please enter a student email address or username.')
                    );
                }
                if (!problemToReset) {
                    return _this.$request_response_error_grade.text(
                        gettext('Please enter a problem location.')
                    );
                }
                sendData = {
                    unique_student_identifier: uniqueStudentIdentifier,
                    problem_to_reset: problemToReset
                };
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: _this.$btn_rescore_problem_single.data('endpoint'),
                    data: sendData,
                    success: _this.clear_errors_then(function() {
                        return alert(edx.StringUtils.interpolate(
                            gettext("Started rescore problem task for problem '<%= problem_id %>' and student '<%= student_id %>'. Click the 'Show Background Task History for Student' button to see the status of the task."),  // jshint ignore:line
                            {
                                student_id: uniqueStudentIdentifier,
                                problem_id: problemToReset
                            }
                        ));
                    }),
                    error: std_ajax_err(function() {
                        return _this.$request_response_error_grade.text(edx.StringUtils.interpolate(
                            gettext("Error starting a task to rescore problem '<%= problem_id %>' for student '<%= student_id %>'. Make sure that the the problem and student identifiers are complete and correct."),  // jshint ignore:line
                            {
                                student_id: uniqueStudentIdentifier,
                                problem_id: problemToReset
                            }
                        ));
                    })
                });
            });
            this.$btn_task_history_single.click(function() {
                var problemToReset, sendData, uniqueStudentIdentifier;
                uniqueStudentIdentifier = _this.$field_student_select_grade.val();
                problemToReset = _this.$field_problem_select_single.val();
                if (!uniqueStudentIdentifier) {
                    return _this.$request_response_error_grade.text(
                        gettext('Please enter a student email address or username.')
                    );
                }
                if (!problemToReset) {
                    return _this.$request_response_error_grade.text(
                        gettext('Please enter a problem location.')
                    );
                }
                sendData = {
                    unique_student_identifier: uniqueStudentIdentifier,
                    problem_location_str: problemToReset
                };
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: _this.$btn_task_history_single.data('endpoint'),
                    data: sendData,
                    success: _this.clear_errors_then(function(data) {
                        return create_task_list_table(_this.$table_task_history_single, data.tasks);
                    }),
                    error: std_ajax_err(function() {
                        return _this.$request_response_error_grade.text(edx.StringUtils.interpolate(
                            gettext("Error getting task history for problem '{problem_id}' and student '{student_id}'. Make sure that the problem and student identifiers are complete and correct."),  // jshint ignore:line
                            {
                                student_id: uniqueStudentIdentifier,
                                problem_id: problemToReset
                            }
                        ));
                    })
                });
            });
            this.$btn_reset_entrance_exam_attempts.click(function() {
                var send_data, unique_student_identifier;
                unique_student_identifier = _this.$field_entrance_exam_student_select_grade.val();
                if (!unique_student_identifier) {
                    return _this.$request_response_error_ee.text(
                        gettext('Please enter a student email address or username.')
                    );
                }
                send_data = {
                    unique_student_identifier: unique_student_identifier,
                    delete_module: false
                };
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: _this.$btn_reset_entrance_exam_attempts.data('endpoint'),
                    data: send_data,
                    success: _this.clear_errors_then(function() {
                        return alert(edx.StringUtils.interpolate(
                            gettext("Entrance exam attempts is being reset for student '{student_id}'."),
                            {student_id: unique_student_identifier}
                        ));
                    }),
                    error: std_ajax_err(function() {
                        return _this.$request_response_error_ee.text(edx.StringUtils.interpolate(
                            gettext("Error resetting entrance exam attempts for student '{student_id}'. Make sure student identifier is correct."),  // jshint ignore:line
                            {student_id: unique_student_identifier}
                        ));
                    })
                });
            });
            this.$btn_rescore_entrance_exam.click(function() {
                var send_data, unique_student_identifier;
                unique_student_identifier = _this.$field_entrance_exam_student_select_grade.val();
                if (!unique_student_identifier) {
                    return _this.$request_response_error_ee.text(
                        gettext('Please enter a student email address or username.')
                    );
                }
                send_data = {
                    unique_student_identifier: unique_student_identifier
                };
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: _this.$btn_rescore_entrance_exam.data('endpoint'),
                    data: send_data,
                    success: _this.clear_errors_then(function() {
                        return alert(edx.StringUtils.interpolate(
                            gettext("Started entrance exam rescore task for student '{student_id}'. Click the 'Show Background Task History for Student' button to see the status of the task."),  // jshint ignore:line
                            {student_id: unique_student_identifier}
                        ));
                    }),
                    error: std_ajax_err(function() {
                        return _this.$request_response_error_ee.text(edx.StringUtils.interpolate(
                            gettext("Error starting a task to rescore entrance exam for student '{student_id}'. Make sure that entrance exam has problems in it and student identifier is correct."),  // jshint ignore:line
                            {student_id: unique_student_identifier}
                        ));
                    })
                });
            });
            this.$btn_skip_entrance_exam.click(function() {
                var confirmMessage, sendData, uniqueStudentIdentifier;
                uniqueStudentIdentifier = _this.$field_entrance_exam_student_select_grade.val();
                if (!uniqueStudentIdentifier) {
                    return _this.$request_response_error_ee.text(
                        gettext("Enter a student's username or email address.")
                    );
                }
                confirmMessage = edx.StringUtils.interpolate(
                    gettext("Do you want to allow this student ('{student_id}') to skip the entrance exam?"),
                    {student_id: uniqueStudentIdentifier}
                );
                if (window.confirm(confirmMessage)) {
                    sendData = {
                        unique_student_identifier: uniqueStudentIdentifier
                    };
                    return $.ajax({
                        dataType: 'json',
                        url: _this.$btn_skip_entrance_exam.data('endpoint'),
                        data: sendData,
                        type: 'POST',
                        success: _this.clear_errors_then(function(data) {
                            return alert(data.message);
                        }),
                        error: std_ajax_err(function() {
                            var error_message;
                            error_message = gettext("An error occurred. Make sure that the student's username or email address is correct and try again.");  // jshint ignore:line
                            return _this.$request_response_error_ee.text(error_message);
                        })
                    });
                }
            });
            this.$btn_delete_entrance_exam_state.click(function() {
                var send_data, unique_student_identifier;
                unique_student_identifier = _this.$field_entrance_exam_student_select_grade.val();
                if (!unique_student_identifier) {
                    return _this.$request_response_error_ee.text(
                        gettext('Please enter a student email address or username.')
                    );
                }
                send_data = {
                    unique_student_identifier: unique_student_identifier,
                    delete_module: true
                };
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: _this.$btn_delete_entrance_exam_state.data('endpoint'),
                    data: send_data,
                    success: _this.clear_errors_then(function() {
                        return alert(edx.StringUtils.interpolate(
                            gettext("Entrance exam state is being deleted for student '{student_id}'."),
                            {student_id: unique_student_identifier}
                        ));
                    }),
                    error: std_ajax_err(function() {
                        return _this.$request_response_error_ee.text(edx.StringUtils.interpolate(
                            gettext("Error deleting entrance exam state for student '{student_id}'. Make sure student identifier is correct."),  // jshint ignore:line
                            {student_id: unique_student_identifier}
                        ));
                    })
                });
            });
            this.$btn_entrance_exam_task_history.click(function() {
                var send_data, unique_student_identifier;
                unique_student_identifier = _this.$field_entrance_exam_student_select_grade.val();
                if (!unique_student_identifier) {
                    return _this.$request_response_error_ee.text(
                        gettext("Enter a student's username or email address.")
                    );
                }
                send_data = {
                    unique_student_identifier: unique_student_identifier
                };
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: _this.$btn_entrance_exam_task_history.data('endpoint'),
                    data: send_data,
                    success: _this.clear_errors_then(function(data) {
                        return create_task_list_table(_this.$table_entrance_exam_task_history, data.tasks);
                    }),
                    error: std_ajax_err(function() {
                        return _this.$request_response_error_ee.text(edx.StringUtils.interpolate(
                            gettext("Error getting entrance exam task history for student '{student_id}'. Make sure student identifier is correct."),  // jshint ignore:line
                            {student_id: unique_student_identifier}
                        ));
                    })
                });
            });
            this.$btn_reset_attempts_all.click(function() {
                var confirmMessage, problemToReset, sendData;
                problemToReset = _this.$field_problem_select_all.val();
                if (!problemToReset) {
                    return _this.$request_response_error_all.text(gettext('Please enter a problem location.'));
                }
                confirmMessage = edx.StringUtils.interpolate(
                    gettext("Reset attempts for all students on problem '{problem_id}'?"),
                    {problem_id: problemToReset}
                );
                if (window.confirm(confirmMessage)) {
                    sendData = {
                        all_students: true,
                        problem_to_reset: problemToReset
                    };
                    return $.ajax({
                        type: 'POST',
                        dataType: 'json',
                        url: _this.$btn_reset_attempts_all.data('endpoint'),
                        data: sendData,
                        success: _this.clear_errors_then(function() {
                            return alert(edx.StringUtils.interpolate(
                                gettext("Successfully started task to reset attempts for problem '{problem_id}'. Click the 'Show Background Task History for Problem' button to see the status of the task."),  // jshint ignore:line
                                {problem_id: problemToReset}
                            ));
                        }),
                        error: std_ajax_err(function() {
                            return _this.$request_response_error_all.text(edx.StringUtils.interpolate(
                                gettext("Error starting a task to reset attempts for all students on problem '{problem_id}'. Make sure that the problem identifier is complete and correct."),  // jshint ignore:line
                                {problem_id: problemToReset}    
                            ));
                        })
                    });
                } else {
                    return _this.clear_errors();
                }
            });
            this.$btn_rescore_problem_all.click(function() {
                var confirmMessage, problemToReset, sendData;
                problemToReset = _this.$field_problem_select_all.val();
                if (!problemToReset) {
                    return _this.$request_response_error_all.text(gettext('Please enter a problem location.'));
                }
                confirmMessage = edx.StringUtils.interpolate(
                    gettext("Rescore problem '{problem_id}' for all students?"),
                    {problem_id: problemToReset}
                );
                if (window.confirm(confirmMessage)) {
                    sendData = {
                        all_students: true,
                        problem_to_reset: problemToReset
                    };
                    return $.ajax({
                        type: 'POST',
                        dataType: 'json',
                        url: _this.$btn_rescore_problem_all.data('endpoint'),
                        data: sendData,
                        success: _this.clear_errors_then(function() {
                            return alert(edx.StringUtils.interpolate(
                                gettext("Successfully started task to rescore problem '{problem_id}' for all students. Click the 'Show Background Task History for Problem' button to see the status of the task."),  // jshint ignore:line
                                {problem_id: problemToReset}
                            ));
                        }),
                        error: std_ajax_err(function() {
                            return _this.$request_response_error_all.text(edx.StringUtils.interpolate(
                                gettext("Error starting a task to rescore problem '{problem_id}'. Make sure that the problem identifier is complete and correct."),  // jshint ignore:line
                                {problem_id: problemToReset}
                            ));
                        })
                    });
                } else {
                    return _this.clear_errors();
                }
            });
            this.$btn_task_history_all.click(function() {
                var send_data;
                send_data = {
                    problem_location_str: _this.$field_problem_select_all.val()
                };
                if (!send_data.problem_location_str) {
                    return _this.$request_response_error_all.text(gettext('Please enter a problem location.'));
                }
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: _this.$btn_task_history_all.data('endpoint'),
                    data: send_data,
                    success: _this.clear_errors_then(function(data) {
                        return create_task_list_table(_this.$table_task_history_all, data.tasks);
                    }),
                    error: std_ajax_err(function() {
                        return _this.$request_response_error_all.text(
                            gettext('Error listing task history for this student and problem.')
                        );
                    })
                });
            });
        }

        StudentAdmin.prototype.clear_errors_then = function(cb) {
            this.$request_response_error_progress.empty();
            this.$request_response_error_grade.empty();
            this.$request_response_error_ee.empty();
            this.$request_response_error_all.empty();
            return function() {
                return cb !== null ? cb.apply(this, arguments) : void 0;
            };
        };

        StudentAdmin.prototype.clear_errors = function() {
            this.$request_response_error_progress.empty();
            this.$request_response_error_grade.empty();
            this.$request_response_error_ee.empty();
            return this.$request_response_error_all.empty();
        };

        StudentAdmin.prototype.onClickTitle = function() {
            return this.instructor_tasks.task_poller.start();
        };

        StudentAdmin.prototype.onExit = function() {
            return this.instructor_tasks.task_poller.stop();
        };

        return StudentAdmin;

    })();

    _.defaults(window, {
        InstructorDashboard: {}
    });

    _.defaults(window.InstructorDashboard, {
        sections: {}
    });

    _.defaults(window.InstructorDashboard.sections, {
        StudentAdmin: window.StudentAdmin
    });

}).call(this);
