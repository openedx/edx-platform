/* globals _, interpolate_text */

(function() {
    'use strict';
    var PendingInstructorTasks, createTaskListTable, findAndAssert, statusAjaxError;

    statusAjaxError = function() {
        return window.InstructorDashboard.util.statusAjaxError.apply(this, arguments);
    };

    createTaskListTable = function() {
        return window.InstructorDashboard.util.createTaskListTable.apply(this, arguments);
    };

    PendingInstructorTasks = function() {
        return window.InstructorDashboard.util.PendingInstructorTasks;
    };

    findAndAssert = function($root, selector) {
        var item, msg;
        item = $root.find(selector);
        if (item.length !== 1) {
            msg = 'Failed Element Selection';
            throw msg;
        } else {
            return item;
        }
    };

    this.StudentAdmin = (function() {
        function StudentAdmin($section) {
            var studentadmin = this;
            this.$section = $section;
            this.$section.data('wrapper', this);
            this.$field_student_select_progress = findAndAssert(this.$section, "input[name='student-select-progress']");
            this.$field_student_select_grade = findAndAssert(this.$section, "input[name='student-select-grade']");
            this.$progress_link = findAndAssert(this.$section, 'a.progress-link');
            this.$field_problem_select_single = findAndAssert(this.$section, "input[name='problem-select-single']");
            this.$btn_reset_attempts_single = findAndAssert(this.$section, "input[name='reset-attempts-single']");
            this.$btn_delete_state_single = this.$section.find("input[name='delete-state-single']");
            this.$btn_rescore_problem_single = this.$section.find("input[name='rescore-problem-single']");
            this.$btn_task_history_single = this.$section.find("input[name='task-history-single']");
            this.$table_task_history_single = this.$section.find('.task-history-single-table');
            this.$field_exam_grade = this.$section.find("input[name='entrance-exam-student-select-grade']");
            this.$btn_reset_entrance_exam_attempts = this.$section.find("input[name='reset-entrance-exam-attempts']");
            this.$btn_delete_entrance_exam_state = this.$section.find("input[name='delete-entrance-exam-state']");
            this.$btn_rescore_entrance_exam = this.$section.find("input[name='rescore-entrance-exam']");
            this.$btn_skip_entrance_exam = this.$section.find("input[name='skip-entrance-exam']");
            this.$btn_entrance_exam_task_history = this.$section.find("input[name='entrance-exam-task-history']");
            this.$table_entrance_exam_task_history = this.$section.find('.entrance-exam-task-history-table');
            this.$field_problem_select_all = this.$section.find("input[name='problem-select-all']");
            this.$btn_reset_attempts_all = this.$section.find("input[name='reset-attempts-all']");
            this.$btn_rescore_problem_all = this.$section.find("input[name='rescore-problem-all']");
            this.$btn_task_history_all = this.$section.find("input[name='task-history-all']");
            this.$table_task_history_all = this.$section.find('.task-history-all-table');
            this.instructor_tasks = new (PendingInstructorTasks())(this.$section);
            this.$request_err = findAndAssert(this.$section, '.student-specific-container .request-response-error');
            this.$request_err_grade = findAndAssert(this.$section, '.student-grade-container .request-response-error');
            this.$request_err_ee = this.$section.find('.entrance-exam-grade-container .request-response-error');
            this.$request_response_error_all = this.$section.find('.course-specific-container .request-response-error');
            this.$progress_link.click(function(e) {
                var errorMessage, fullErrorMessage, uniqStudentIdentifier;
                e.preventDefault();
                uniqStudentIdentifier = studentadmin.$field_student_select_progress.val();
                if (!uniqStudentIdentifier) {
                    return studentadmin.$request_err.text(
                        gettext('Please enter a student email address or username.')
                    );
                }
                errorMessage = gettext("Error getting student progress url for '<%- student_id %>'. Make sure that the student identifier is spelled correctly.");  // eslint-disable-line max-len
                fullErrorMessage = _.template(errorMessage)({
                    student_id: uniqStudentIdentifier
                });
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: studentadmin.$progress_link.data('endpoint'),
                    data: {
                        unique_student_identifier: uniqStudentIdentifier
                    },
                    success: studentadmin.clear_errors_then(function(data) {
                        window.location = data.progress_url;
                        return window.location;
                    }),
                    error: statusAjaxError(function() {
                        return studentadmin.$request_err.text(fullErrorMessage);
                    })
                });
            });
            this.$btn_reset_attempts_single.click(function() {
                var errorMessage, fullErrorMessage, fullSuccessMessage,
                    problemToReset, sendData, successMessage, uniqStudentIdentifier;
                uniqStudentIdentifier = studentadmin.$field_student_select_grade.val();
                problemToReset = studentadmin.$field_problem_select_single.val();
                if (!uniqStudentIdentifier) {
                    return studentadmin.$request_err_grade.text(
                        gettext('Please enter a student email address or username.')
                    );
                }
                if (!problemToReset) {
                    return studentadmin.$request_err_grade.text(gettext('Please enter a problem location.'));
                }
                sendData = {
                    unique_student_identifier: uniqStudentIdentifier,
                    problem_to_reset: problemToReset,
                    delete_module: false
                };
                successMessage = gettext("Success! Problem attempts reset for problem '<%- problem_id %>' and student '<%- student_id %>'.");  // eslint-disable-line max-len
                errorMessage = gettext("Error resetting problem attempts for problem '<%= problem_id %>' and student '<%- student_id %>'. Make sure that the problem and student identifiers are complete and correct.");  // eslint-disable-line max-len
                fullSuccessMessage = _.template(successMessage)({
                    problem_id: problemToReset,
                    student_id: uniqStudentIdentifier
                });
                fullErrorMessage = _.template(errorMessage)({
                    problem_id: problemToReset,
                    student_id: uniqStudentIdentifier
                });
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: studentadmin.$btn_reset_attempts_single.data('endpoint'),
                    data: sendData,
                    success: studentadmin.clear_errors_then(function() {
                        return alert(fullSuccessMessage);  // eslint-disable-line no-alert
                    }),
                    error: statusAjaxError(function() {
                        return studentadmin.$request_err_grade.text(fullErrorMessage);
                    })
                });
            });
            this.$btn_delete_state_single.click(function() {
                var confirmMessage, errorMessage, fullConfirmMessage,
                    fullErrorMessage, problemToReset, sendData, uniqStudentIdentifier;
                uniqStudentIdentifier = studentadmin.$field_student_select_grade.val();
                problemToReset = studentadmin.$field_problem_select_single.val();
                if (!uniqStudentIdentifier) {
                    return studentadmin.$request_err_grade.text(
                        gettext('Please enter a student email address or username.')
                    );
                }
                if (!problemToReset) {
                    return studentadmin.$request_err_grade.text(
                        gettext('Please enter a problem location.')
                    );
                }
                confirmMessage = gettext("Delete student '<%- student_id %>'s state on problem '<%- problem_id %>'?");
                fullConfirmMessage = _.template(confirmMessage)({
                    student_id: uniqStudentIdentifier,
                    problem_id: problemToReset
                });
                if (window.confirm(fullConfirmMessage)) {  // eslint-disable-line no-alert
                    sendData = {
                        unique_student_identifier: uniqStudentIdentifier,
                        problem_to_reset: problemToReset,
                        delete_module: true
                    };
                    errorMessage = gettext("Error deleting student '<%- student_id %>'s state on problem '<%- problem_id %>'. Make sure that the problem and student identifiers are complete and correct.");  // eslint-disable-line max-len
                    fullErrorMessage = _.template(errorMessage)({
                        student_id: uniqStudentIdentifier,
                        problem_id: problemToReset
                    });
                    return $.ajax({
                        type: 'POST',
                        dataType: 'json',
                        url: studentadmin.$btn_delete_state_single.data('endpoint'),
                        data: sendData,
                        success: studentadmin.clear_errors_then(function() {
                            return alert(gettext('Module state successfully deleted.'));  // eslint-disable-line no-alert, max-len
                        }),
                        error: statusAjaxError(function() {
                            return studentadmin.$request_err_grade.text(fullErrorMessage);
                        })
                    });
                } else {
                    return studentadmin.clear_errors();
                }
            });
            this.$btn_rescore_problem_single.click(function() {
                var errorMessage, fullErrorMessage, fullSuccessMessage,
                    problemToReset, sendData, successMessage, uniqStudentIdentifier;
                uniqStudentIdentifier = studentadmin.$field_student_select_grade.val();
                problemToReset = studentadmin.$field_problem_select_single.val();
                if (!uniqStudentIdentifier) {
                    return studentadmin.$request_err_grade.text(
                        gettext('Please enter a student email address or username.')
                    );
                }
                if (!problemToReset) {
                    return studentadmin.$request_err_grade.text(
                        gettext('Please enter a problem location.')
                    );
                }
                sendData = {
                    unique_student_identifier: uniqStudentIdentifier,
                    problem_to_reset: problemToReset
                };
                successMessage = gettext("Started rescore problem task for problem '<%- problem_id %>' and student '<%- student_id %>'. Click the 'Show Background Task History for Student' button to see the status of the task.");  // eslint-disable-line max-len
                fullSuccessMessage = _.template(successMessage)({
                    student_id: uniqStudentIdentifier,
                    problem_id: problemToReset
                });
                errorMessage = gettext("Error starting a task to rescore problem '<%- problem_id %>' for student '<%- student_id %>'. Make sure that the the problem and student identifiers are complete and correct.");  // eslint-disable-line max-len
                fullErrorMessage = _.template(errorMessage)({
                    student_id: uniqStudentIdentifier,
                    problem_id: problemToReset
                });
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: studentadmin.$btn_rescore_problem_single.data('endpoint'),
                    data: sendData,
                    success: studentadmin.clear_errors_then(function() {
                        return alert(fullSuccessMessage);  // eslint-disable-line no-alert
                    }),
                    error: statusAjaxError(function() {
                        return studentadmin.$request_err_grade.text(fullErrorMessage);
                    })
                });
            });
            this.$btn_task_history_single.click(function() {
                var errorMessage, fullErrorMessage, problemToReset, sendData, uniqStudentIdentifier;
                uniqStudentIdentifier = studentadmin.$field_student_select_grade.val();
                problemToReset = studentadmin.$field_problem_select_single.val();
                if (!uniqStudentIdentifier) {
                    return studentadmin.$request_err_grade.text(
                        gettext('Please enter a student email address or username.')
                    );
                }
                if (!problemToReset) {
                    return studentadmin.$request_err_grade.text(
                        gettext('Please enter a problem location.')
                    );
                }
                sendData = {
                    unique_student_identifier: uniqStudentIdentifier,
                    problem_location_str: problemToReset
                };
                errorMessage = gettext("Error getting task history for problem '<%- problem_id %>' and student '<%- student_id %>'. Make sure that the problem and student identifiers are complete and correct.");  // eslint-disable-line max-len
                fullErrorMessage = _.template(errorMessage)({
                    student_id: uniqStudentIdentifier,
                    problem_id: problemToReset
                });
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: studentadmin.$btn_task_history_single.data('endpoint'),
                    data: sendData,
                    success: studentadmin.clear_errors_then(function(data) {
                        return createTaskListTable(studentadmin.$table_task_history_single, data.tasks);
                    }),
                    error: statusAjaxError(function() {
                        return studentadmin.$request_err_grade.text(fullErrorMessage);
                    })
                });
            });
            this.$btn_reset_entrance_exam_attempts.click(function() {
                var sendData, uniqStudentIdentifier;
                uniqStudentIdentifier = studentadmin.$field_exam_grade.val();
                if (!uniqStudentIdentifier) {
                    return studentadmin.$request_err_ee.text(gettext(
                        'Please enter a student email address or username.')
                    );
                }
                sendData = {
                    unique_student_identifier: uniqStudentIdentifier,
                    delete_module: false
                };
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: studentadmin.$btn_reset_entrance_exam_attempts.data('endpoint'),
                    data: sendData,
                    success: studentadmin.clear_errors_then(function() {
                        var fullSuccessMessage, successMessage;
                        successMessage = gettext("Entrance exam attempts is being reset for student '{student_id}'.");
                        fullSuccessMessage = interpolate_text(successMessage, {
                            student_id: uniqStudentIdentifier
                        });
                        return alert(fullSuccessMessage);  // eslint-disable-line no-alert
                    }),
                    error: statusAjaxError(function() {
                        var errorMessage, fullErrorMessage;
                        errorMessage = gettext("Error resetting entrance exam attempts for student '{student_id}'. Make sure student identifier is correct.");  // eslint-disable-line max-len
                        fullErrorMessage = interpolate_text(errorMessage, {
                            student_id: uniqStudentIdentifier
                        });
                        return studentadmin.$request_err_ee.text(fullErrorMessage);
                    })
                });
            });
            this.$btn_rescore_entrance_exam.click(function() {
                var sendData, uniqStudentIdentifier;
                uniqStudentIdentifier = studentadmin.$field_exam_grade.val();
                if (!uniqStudentIdentifier) {
                    return studentadmin.$request_err_ee.text(gettext(
                        'Please enter a student email address or username.')
                    );
                }
                sendData = {
                    unique_student_identifier: uniqStudentIdentifier
                };
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: studentadmin.$btn_rescore_entrance_exam.data('endpoint'),
                    data: sendData,
                    success: studentadmin.clear_errors_then(function() {
                        var fullSuccessMessage, successMessage;
                        successMessage = gettext("Started entrance exam rescore task for student '{student_id}'. Click the 'Show Background Task History for Student' button to see the status of the task.");  // eslint-disable-line max-len
                        fullSuccessMessage = interpolate_text(successMessage, {
                            student_id: uniqStudentIdentifier
                        });
                        return alert(fullSuccessMessage);  // eslint-disable-line no-alert
                    }),
                    error: statusAjaxError(function() {
                        var errorMessage, fullErrorMessage;
                        errorMessage = gettext("Error starting a task to rescore entrance exam for student '{student_id}'. Make sure that entrance exam has problems in it and student identifier is correct.");  // eslint-disable-line max-len
                        fullErrorMessage = interpolate_text(errorMessage, {
                            student_id: uniqStudentIdentifier
                        });
                        return studentadmin.$request_err_ee.text(fullErrorMessage);
                    })
                });
            });
            this.$btn_skip_entrance_exam.click(function() {
                var confirmMessage, fullConfirmMessage, sendData, uniqStudentIdentifier;
                uniqStudentIdentifier = studentadmin.$field_exam_grade.val();
                if (!uniqStudentIdentifier) {
                    return studentadmin.$request_err_ee.text(gettext("Enter a student's username or email address."));
                }
                confirmMessage = gettext("Do you want to allow this student ('{student_id}') to skip the entrance exam?");  // eslint-disable-line max-len
                fullConfirmMessage = interpolate_text(confirmMessage, {
                    student_id: uniqStudentIdentifier
                });
                if (window.confirm(fullConfirmMessage)) {  // eslint-disable-line no-alert
                    sendData = {
                        unique_student_identifier: uniqStudentIdentifier
                    };
                    return $.ajax({
                        dataType: 'json',
                        url: studentadmin.$btn_skip_entrance_exam.data('endpoint'),
                        data: sendData,
                        type: 'POST',
                        success: studentadmin.clear_errors_then(function(data) {
                            return alert(data.message);  // eslint-disable-line no-alert
                        }),
                        error: statusAjaxError(function() {
                            var errorMessage;
                            errorMessage = gettext("An error occurred. Make sure that the student's username or email address is correct and try again.");  // eslint-disable-line max-len
                            return studentadmin.$request_err_ee.text(errorMessage);
                        })
                    });
                }
                return false;
            });
            this.$btn_delete_entrance_exam_state.click(function() {
                var sendData, uniqStudentIdentifier;
                uniqStudentIdentifier = studentadmin.$field_exam_grade.val();
                if (!uniqStudentIdentifier) {
                    return studentadmin.$request_err_ee.text(
                        gettext('Please enter a student email address or username.')
                    );
                }
                sendData = {
                    unique_student_identifier: uniqStudentIdentifier,
                    delete_module: true
                };
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: studentadmin.$btn_delete_entrance_exam_state.data('endpoint'),
                    data: sendData,
                    success: studentadmin.clear_errors_then(function() {
                        var fullSuccessMessage, successMessage;
                        successMessage = gettext("Entrance exam state is being deleted for student '{student_id}'.");
                        fullSuccessMessage = interpolate_text(successMessage, {
                            student_id: uniqStudentIdentifier
                        });
                        return alert(fullSuccessMessage);  // eslint-disable-line no-alert
                    }),
                    error: statusAjaxError(function() {
                        var errorMessage, fullErrorMessage;
                        errorMessage = gettext("Error deleting entrance exam state for student '{student_id}'. Make sure student identifier is correct.");  // eslint-disable-line max-len
                        fullErrorMessage = interpolate_text(errorMessage, {
                            student_id: uniqStudentIdentifier
                        });
                        return studentadmin.$request_err_ee.text(fullErrorMessage);
                    })
                });
            });
            this.$btn_entrance_exam_task_history.click(function() {
                var sendData, uniqStudentIdentifier;
                uniqStudentIdentifier = studentadmin.$field_exam_grade.val();
                if (!uniqStudentIdentifier) {
                    return studentadmin.$request_err_ee.text(
                        gettext("Enter a student's username or email address.")
                    );
                }
                sendData = {
                    unique_student_identifier: uniqStudentIdentifier
                };
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: studentadmin.$btn_entrance_exam_task_history.data('endpoint'),
                    data: sendData,
                    success: studentadmin.clear_errors_then(function(data) {
                        return createTaskListTable(studentadmin.$table_entrance_exam_task_history, data.tasks);
                    }),
                    error: statusAjaxError(function() {
                        var errorMessage, fullErrorMessage;
                        errorMessage = gettext("Error getting entrance exam task history for student '{student_id}'. Make sure student identifier is correct.");  // eslint-disable-line max-len
                        fullErrorMessage = interpolate_text(errorMessage, {
                            student_id: uniqStudentIdentifier
                        });
                        return studentadmin.$request_err_ee.text(fullErrorMessage);
                    })
                });
            });
            this.$btn_reset_attempts_all.click(function() {
                var confirmMessage, errorMessage, fullConfirmMessage,
                    fullErrorMessage, fullSuccessMessage, problemToReset, sendData, successMessage;
                problemToReset = studentadmin.$field_problem_select_all.val();
                if (!problemToReset) {
                    return studentadmin.$request_response_error_all.text(
                        gettext('Please enter a problem location.')
                    );
                }
                confirmMessage = gettext("Reset attempts for all students on problem '<%- problem_id %>'?");
                fullConfirmMessage = _.template(confirmMessage)({
                    problem_id: problemToReset
                });
                if (window.confirm(fullConfirmMessage)) { // eslint-disable-line no-alert
                    sendData = {
                        all_students: true,
                        problem_to_reset: problemToReset
                    };
                    successMessage = gettext("Successfully started task to reset attempts for problem '<%- problem_id %>'. Click the 'Show Background Task History for Problem' button to see the status of the task.");  // eslint-disable-line max-len
                    fullSuccessMessage = _.template(successMessage)({
                        problem_id: problemToReset
                    });
                    errorMessage = gettext("Error starting a task to reset attempts for all students on problem '<%- problem_id %>'. Make sure that the problem identifier is complete and correct.");  // eslint-disable-line max-len
                    fullErrorMessage = _.template(errorMessage)({
                        problem_id: problemToReset
                    });
                    return $.ajax({
                        type: 'POST',
                        dataType: 'json',
                        url: studentadmin.$btn_reset_attempts_all.data('endpoint'),
                        data: sendData,
                        success: studentadmin.clear_errors_then(function() {
                            return alert(fullSuccessMessage);  // eslint-disable-line no-alert
                        }),
                        error: statusAjaxError(function() {
                            return studentadmin.$request_response_error_all.text(fullErrorMessage);
                        })
                    });
                } else {
                    return studentadmin.clear_errors();
                }
            });
            this.$btn_rescore_problem_all.click(function() {
                var confirmMessage, errorMessage, fullConfirmMessage,
                    fullErrorMessage, fullSuccessMessage, problemToReset, sendData, successMessage;
                problemToReset = studentadmin.$field_problem_select_all.val();
                if (!problemToReset) {
                    return studentadmin.$request_response_error_all.text(
                        gettext('Please enter a problem location.')
                    );
                }
                confirmMessage = gettext("Rescore problem '<%- problem_id %>' for all students?");
                fullConfirmMessage = _.template(confirmMessage)({
                    problem_id: problemToReset
                });
                if (window.confirm(fullConfirmMessage)) {  // eslint-disable-line no-alert
                    sendData = {
                        all_students: true,
                        problem_to_reset: problemToReset
                    };
                    successMessage = gettext("Successfully started task to rescore problem '<%- problem_id %>' for all students. Click the 'Show Background Task History for Problem' button to see the status of the task.");  // eslint-disable-line max-len
                    fullSuccessMessage = _.template(successMessage)({
                        problem_id: problemToReset
                    });
                    errorMessage = gettext("Error starting a task to rescore problem '<%- problem_id %>'. Make sure that the problem identifier is complete and correct.");  // eslint-disable-line max-len
                    fullErrorMessage = _.template(errorMessage)({
                        problem_id: problemToReset
                    });
                    return $.ajax({
                        type: 'POST',
                        dataType: 'json',
                        url: studentadmin.$btn_rescore_problem_all.data('endpoint'),
                        data: sendData,
                        success: studentadmin.clear_errors_then(function() {
                            return alert(fullSuccessMessage);  // eslint-disable-line no-alert
                        }),
                        error: statusAjaxError(function() {
                            return studentadmin.$request_response_error_all.text(fullErrorMessage);
                        })
                    });
                } else {
                    return studentadmin.clear_errors();
                }
            });
            this.$btn_task_history_all.click(function() {
                var sendData;
                sendData = {
                    problem_location_str: studentadmin.$field_problem_select_all.val()
                };
                if (!sendData.problem_location_str) {
                    return studentadmin.$request_response_error_all.text(
                        gettext('Please enter a problem location.')
                    );
                }
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: studentadmin.$btn_task_history_all.data('endpoint'),
                    data: sendData,
                    success: studentadmin.clear_errors_then(function(data) {
                        return createTaskListTable(studentadmin.$table_task_history_all, data.tasks);
                    }),
                    error: statusAjaxError(function() {
                        return studentadmin.$request_response_error_all.text(
                            gettext('Error listing task history for this student and problem.')
                        );
                    })
                });
            });
        }

        StudentAdmin.prototype.clear_errors_then = function(cb) {
            this.$request_err.empty();
            this.$request_err_grade.empty();
            this.$request_err_ee.empty();
            this.$request_response_error_all.empty();
            return function() {
                return cb != null ? cb.apply(this, arguments) : void 0;
            };
        };

        StudentAdmin.prototype.clear_errors = function() {
            this.$request_err.empty();
            this.$request_err_grade.empty();
            this.$request_err_ee.empty();
            return this.$request_response_error_all.empty();
        };

        StudentAdmin.prototype.onClickTitle = function() {
            return this.instructor_tasks.task_poller.start();
        };

        StudentAdmin.prototype.onExit = function() {
            return this.instructor_tasks.task_poller.stop();
        };

        return StudentAdmin;
    }());

    _.defaults(window, {
        InstructorDashboard: {}
    });

    _.defaults(window.InstructorDashboard, {
        sections: {}
    });

    _.defaults(window.InstructorDashboard.sections, {
        StudentAdmin: this.StudentAdmin
    });
}).call(this);
