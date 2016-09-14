/*global define, onCertificatesReady */
define([
        'jquery',
        'common/js/spec_helpers/ajax_helpers',
        'js/instructor_dashboard/certificates'
    ],
    function($, AjaxHelpers) {
        'use strict';
        describe("edx.instructor_dashboard.certificates.regenerate_certificates", function() {
            var $regenerate_certificates_button = null,
                $certificate_regeneration_status = null,
                requests = null;
            var MESSAGES = {
                success_message: 'Certificate regeneration task has been started. ' +
                    'You can view the status of the generation task in the "Pending Tasks" section.',
                error_message: 'Please select one or more certificate statuses that require certificate regeneration.',
                server_error_message: "Error while regenerating certificates. Please try again."
            };
            var expected = {
                error_class: 'msg-error',
                success_class: 'msg-success',
                url: 'test/url/',
                postData : [],
                selected_statuses: ['downloadable', 'error'],
                body: 'certificate_statuses=downloadable&certificate_statuses=error'
            };

            var select_options = function(option_values){
                $.each(option_values, function(index, element){
                    $("#certificate-statuses option[value=" + element + "]").attr('selected', 'selected');
                });
            };

            beforeEach(function() {
                var fixture = '<section id = "certificates"><h2>Regenerate Certificates</h2>' +
                    '<form id="certificate-regenerating-form" method="post" action="' + expected.url + '">' +
                    '   <p id="status-multi-select-tip">Select one or more certificate statuses ' +
                    '       below using your mouse and ctrl or command key.</p>' +
                    '   <select class="multi-select" multiple id="certificate-statuses" ' +
                    '       name="certificate_statuses" aria-describedby="status-multi-select-tip">' +
                    '       <option value="downloadable">Downloadable (2)</option>' +
                    '       <option value="error">Error (2)</option>' +
                    '       <option value="generating">Generating (1)</option>' +
                    '   </select>' +
                    '   <label for="certificate-statuses">' +
                    '       Select certificate statuses that need regeneration and click Regenerate ' +
                    '       Certificates button.' +
                    '   </label>' +
                    '   <input type="button" id="btn-start-regenerating-certificates" value="Regenerate Certificates"' +
                    '   data-endpoint="' + expected.url + '"/>' +
                    '</form>' +
                    '<div class="message certificate-regeneration-status"></div></section>';

                setFixtures(fixture);
                onCertificatesReady();
                $regenerate_certificates_button = $("#btn-start-regenerating-certificates");
                $certificate_regeneration_status = $(".certificate-regeneration-status");
                requests = AjaxHelpers.requests(this);
            });

            it("does not regenerate certificates if user cancels operation in confirm popup", function() {
                spyOn(window, 'confirm').andReturn(false);
                $regenerate_certificates_button.click();
                expect(window.confirm).toHaveBeenCalled();
                AjaxHelpers.expectNoRequests(requests);
            });

            it("sends regenerate certificates request if user accepts operation in confirm popup", function() {
                spyOn(window, 'confirm').andReturn(true);
                $regenerate_certificates_button.click();
                expect(window.confirm).toHaveBeenCalled();
                AjaxHelpers.expectRequest(requests, 'POST', expected.url);
            });

            it("sends regenerate certificates request with selected certificate statuses", function() {
                spyOn(window, 'confirm').andReturn(true);

                select_options(expected.selected_statuses);

                $regenerate_certificates_button.click();
                AjaxHelpers.expectRequest(requests, 'POST', expected.url, expected.body);
            });

            it("displays error message in case of server side error", function() {
                spyOn(window, 'confirm').andReturn(true);
                select_options(expected.selected_statuses);

                $regenerate_certificates_button.click();
                AjaxHelpers.respondWithError(requests, 500, {message: MESSAGES.server_error_message});
                expect($certificate_regeneration_status).toHaveClass(expected.error_class);
                expect($certificate_regeneration_status.text()).toEqual(MESSAGES.server_error_message);
            });

            it("displays error message returned by the server in case of unsuccessful request", function() {
                spyOn(window, 'confirm').andReturn(true);
                select_options(expected.selected_statuses);

                $regenerate_certificates_button.click();
                AjaxHelpers.respondWithError(requests, 400, {message: MESSAGES.error_message});
                expect($certificate_regeneration_status).toHaveClass(expected.error_class);
                expect($certificate_regeneration_status.text()).toEqual(MESSAGES.error_message);
            });

            it("displays success message returned by the server in case of successful request", function() {
                spyOn(window, 'confirm').andReturn(true);
                select_options(expected.selected_statuses);

                $regenerate_certificates_button.click();
                AjaxHelpers.respondWithJson(requests, {message: MESSAGES.success_message, success: true});
                expect($certificate_regeneration_status).toHaveClass(expected.success_class);
                expect($certificate_regeneration_status.text()).toEqual(MESSAGES.success_message);
            });

        });
    }
);
