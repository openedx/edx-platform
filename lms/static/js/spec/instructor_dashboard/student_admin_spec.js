define(['jquery', 'coffee/src/instructor_dashboard/student_admin', 'common/js/spec_helpers/ajax_helpers'],
    function ($, StudentAdmin, AjaxHelpers) {
        //'coffee/src/instructor_dashboard/student_admin'
        'use strict';
        describe("edx.instructor_dashboard.student_admin.StudentAdmin", function() {
            var studentadmin, dashboard_api_url, unique_student_identifier, alert_msg;

            beforeEach(function() {
                loadFixtures('js/fixtures/instructor_dashboard/student_admin.html');
                window.InstructorDashboard = {};
                window.InstructorDashboard.util = {
                    std_ajax_err: std_ajax_err,
                    PendingInstructorTasks: PendingInstructorTasks,
                    create_task_list_table: create_task_list_table
                };
                studentadmin = new window.StudentAdmin($('#student_admin'));
                dashboard_api_url = '/courses/PU/FSc/2014_T4/instructor/api';
                unique_student_identifier = "test@example.com";
                alert_msg = '';
                spyOn(window, 'alert').andCallFake(function(message) {
                    alert_msg = message;
                });

            });

            it('initiates resetting of entrance exam when button is clicked', function() {
                studentadmin.$btn_reset_entrance_exam_attempts.click();
                // expect error to be shown since student identifier is not set
                expect(studentadmin.$request_response_error_ee.text()).toEqual(gettext("Please enter a student email address or username."));

                var success_message = gettext("Entrance exam attempts is being reset for student '{student_id}'.");
                var full_success_message = interpolate_text(success_message, {
                  student_id: unique_student_identifier
                });

                // Spy on AJAX requests
                var requests = AjaxHelpers.requests(this);

                studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier);
                studentadmin.$btn_reset_entrance_exam_attempts.click();
                // Verify that the client contacts the server to start instructor task
                var params = $.param({
                    unique_student_identifier: unique_student_identifier,
                    delete_module: false
                });
                var url = dashboard_api_url + '/reset_student_attempts_for_entrance_exam';
                AjaxHelpers.expectPostRequest(requests, url, params);

                // Simulate a success response from the server
                AjaxHelpers.respondWithJson(requests, {
                    message: full_success_message
                });
                expect(alert_msg).toEqual(full_success_message);
            });

            it('shows an error when resetting of entrance exam fails', function() {
                // Spy on AJAX requests
                var requests = AjaxHelpers.requests(this);
                studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
                studentadmin.$btn_reset_entrance_exam_attempts.click();
                // Verify that the client contacts the server to start instructor task
                var params = $.param({
                    unique_student_identifier: unique_student_identifier,
                    delete_module: false
                });
                var url = dashboard_api_url + '/reset_student_attempts_for_entrance_exam';
                AjaxHelpers.expectPostRequest(requests, url, params);

                // Simulate an error response from the server
                AjaxHelpers.respondWithError(requests, 400,{});

                var error_message = gettext("Error resetting entrance exam attempts for student '{student_id}'. Make sure student identifier is correct.");
                var full_error_message = interpolate_text(error_message, {
                  student_id: unique_student_identifier
                });
                expect(studentadmin.$request_response_error_ee.text()).toEqual(full_error_message);
            });

            it('initiates rescoring of the entrance exam when the button is clicked', function() {
                studentadmin.$btn_rescore_entrance_exam.click();
                // expect error to be shown since student identifier is not set
                expect(studentadmin.$request_response_error_ee.text()).toEqual(gettext("Please enter a student email address or username."));

                var success_message = gettext("Started entrance exam rescore task for student '{student_id}'." +
                    " Click the 'Show Background Task History for Student' button to see the status of the task.");
                var full_success_message = interpolate_text(success_message, {
                  student_id: unique_student_identifier
                });

                // Spy on AJAX requests
                var requests = AjaxHelpers.requests(this);

                studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
                studentadmin.$btn_rescore_entrance_exam.click();
                // Verify that the client contacts the server to start instructor task
                var params = $.param({
                    unique_student_identifier: unique_student_identifier
                });
                var url = dashboard_api_url + '/rescore_entrance_exam';
                AjaxHelpers.expectPostRequest(requests, url, params);

                // Simulate a success response from the server
                AjaxHelpers.respondWithJson(requests, {
                    message: full_success_message
                });
                expect(alert_msg).toEqual(full_success_message);
            });

            it('shows an error when entrance exam rescoring fails', function() {
                // Spy on AJAX requests
                var requests = AjaxHelpers.requests(this);
                studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
                studentadmin.$btn_rescore_entrance_exam.click();
                // Verify that the client contacts the server to start instructor task
                var params = $.param({
                    unique_student_identifier: unique_student_identifier
                });
                var url = dashboard_api_url + '/rescore_entrance_exam';
                AjaxHelpers.expectPostRequest(requests, url, params);

                // Simulate an error response from the server
                AjaxHelpers.respondWithError(requests, 400,{});

                var error_message = gettext("Error starting a task to rescore entrance exam for student '{student_id}'." +
                    " Make sure that entrance exam has problems in it and student identifier is correct.");
                var full_error_message = interpolate_text(error_message, {
                  student_id: unique_student_identifier
                });
                expect(studentadmin.$request_response_error_ee.text()).toEqual(full_error_message);
            });

            it('initiates skip entrance exam when button is clicked', function() {
                studentadmin.$btn_skip_entrance_exam.click();
                // expect error to be shown since student identifier is not set
                expect(studentadmin.$request_response_error_ee.text()).toEqual(gettext("Enter a student's username or email address."));

                var success_message = "This student ('{student_id}') will skip the entrance exam.";
                var full_success_message = interpolate_text(success_message, {
                  student_id: unique_student_identifier
                });

                // Spy on AJAX requests
                var requests = AjaxHelpers.requests(this);

                studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
                studentadmin.$btn_skip_entrance_exam.click();
                // Verify that the client contacts the server to start instructor task
                var url = dashboard_api_url + '/mark_student_can_skip_entrance_exam';
                AjaxHelpers.expectRequest(requests, 'POST', url, $.param({
                    'unique_student_identifier': unique_student_identifier
                }));

                // Simulate a success response from the server
                AjaxHelpers.respondWithJson(requests, {
                    message: full_success_message
                });
                expect(alert_msg).toEqual(full_success_message);
            });

            it('shows an error when skip entrance exam fails', function() {
                // Spy on AJAX requests
                var requests = AjaxHelpers.requests(this);
                studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
                studentadmin.$btn_skip_entrance_exam.click();
                // Verify that the client contacts the server to start instructor task
                var url = dashboard_api_url + '/mark_student_can_skip_entrance_exam';
                AjaxHelpers.expectRequest(requests, 'POST', url, $.param({
                    'unique_student_identifier': unique_student_identifier
                }));

                // Simulate an error response from the server
                AjaxHelpers.respondWithError(requests, 400,{});

                var error_message = "An error occurred. Make sure that the student's username or email address is correct and try again.";
                expect(studentadmin.$request_response_error_ee.text()).toEqual(error_message);
            });

            it('initiates delete student state for entrance exam when button is clicked', function() {
                studentadmin.$btn_delete_entrance_exam_state.click();
                // expect error to be shown since student identifier is not set
                expect(studentadmin.$request_response_error_ee.text()).toEqual(gettext("Please enter a student email address or username."));

                var success_message = gettext("Entrance exam state is being deleted for student '{student_id}'.");
                var full_success_message = interpolate_text(success_message, {
                  student_id: unique_student_identifier
                });

                // Spy on AJAX requests
                var requests = AjaxHelpers.requests(this);

                studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
                studentadmin.$btn_delete_entrance_exam_state.click();
                // Verify that the client contacts the server to start instructor task
                var params = $.param({
                    unique_student_identifier: unique_student_identifier,
                    delete_module: true
                });
                var url = dashboard_api_url + '/reset_student_attempts_for_entrance_exam';
                AjaxHelpers.expectPostRequest(requests, url, params);

                // Simulate a success response from the server
                AjaxHelpers.respondWithJson(requests, {
                    message: full_success_message
                });
                expect(alert_msg).toEqual(full_success_message);
            });

            it('shows an error when delete student state for entrance exam fails', function() {
                // Spy on AJAX requests
                var requests = AjaxHelpers.requests(this);
                studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
                studentadmin.$btn_delete_entrance_exam_state.click();
                // Verify that the client contacts the server to start instructor task
                var params = $.param({
                    unique_student_identifier: unique_student_identifier,
                    delete_module: true
                });
                var url = dashboard_api_url + '/reset_student_attempts_for_entrance_exam';
                AjaxHelpers.expectPostRequest(requests, url, params);

                // Simulate an error response from the server
                AjaxHelpers.respondWithError(requests, 400,{});

                var error_message = gettext("Error deleting entrance exam state for student '{student_id}'. " +
                    "Make sure student identifier is correct.");
                var full_error_message = interpolate_text(error_message, {
                  student_id: unique_student_identifier
                });
                expect(studentadmin.$request_response_error_ee.text()).toEqual(full_error_message);
            });

            it('initiates listing of entrance exam task history when button is clicked', function() {
                studentadmin.$btn_entrance_exam_task_history.click();
                // expect error to be shown since student identifier is not set
                expect(studentadmin.$request_response_error_ee.text()).toEqual(gettext("Enter a student's username or email address."));

                var success_message = gettext("Entrance exam state is being deleted for student '{student_id}'.");
                var full_success_message = interpolate_text(success_message, {
                  student_id: unique_student_identifier
                });

                // Spy on AJAX requests
                var requests = AjaxHelpers.requests(this);

                studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
                studentadmin.$btn_entrance_exam_task_history.click();
                // Verify that the client contacts the server to start instructor task
                var params = $.param({
                    unique_student_identifier: unique_student_identifier
                });
                var url = dashboard_api_url + '/list_entrance_exam_instructor_tasks';
                AjaxHelpers.expectPostRequest(requests, url, params);

                // Simulate a success response from the server
                AjaxHelpers.respondWithJson(requests, {
                    "tasks": [
                        {
                            "status": "Incomplete",
                            "task_type": "rescore_problem",
                            "task_id": "9955d413-eac1-441f-978d-27c60dd1c946",
                            "created": "2015-02-19T10:59:01+00:00",
                            "task_input": "{\"entrance_exam_url\": \"i4x://PU/FSc/chapter/d2204197cce443c4a0d5c852d4e7f638\", \"student\": \"audit\"}",
                            "duration_sec": "unknown",
                            "task_message": "No status information available",
                            "requester": "staff",
                            "task_state": "QUEUING"
                        }
                    ]
                });
                expect($('.entrance-exam-task-history-table')).toBeVisible();
            });

            it('shows an error when listing entrance exam task history fails', function() {
                // Spy on AJAX requests
                var requests = AjaxHelpers.requests(this);
                studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
                studentadmin.$btn_entrance_exam_task_history.click();
                // Verify that the client contacts the server to start instructor task
                var params = $.param({
                    unique_student_identifier: unique_student_identifier
                });
                var url = dashboard_api_url + '/list_entrance_exam_instructor_tasks';
                AjaxHelpers.expectPostRequest(requests, url, params);

                // Simulate an error response from the server
                AjaxHelpers.respondWithError(requests, 400,{});

                var error_message = gettext("Error getting entrance exam task history for student '{student_id}'. " +
                    "Make sure student identifier is correct.");
                var full_error_message = interpolate_text(error_message, {
                  student_id: unique_student_identifier
                });
                expect(studentadmin.$request_response_error_ee.text()).toEqual(full_error_message);
            });

        });
    });
