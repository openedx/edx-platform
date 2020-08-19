/* global define */
define(['jquery',
    'js/instructor_dashboard/data_download',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'slick.grid'],
    function($, DataDownload, AjaxHelpers) {
        'use strict';
        describe('edx.instructor_dashboard.data_download.DataDownload_Certificate', function() {
            var url, dataDownloadCertificates;

            beforeEach(function() {
                loadFixtures('js/fixtures/instructor_dashboard/data_download.html');
                dataDownloadCertificates = new window.DataDownload_Certificate($('.issued_certificates'));
                url = '/courses/PU/FSc/2014_T4/instructor/api/get_issued_certificates';
                dataDownloadCertificates.$list_issued_certificate_table_btn.data('endpoint', url);
            });

            it('show data on success callback', function() {
                // Spy on AJAX requests
                var requests = AjaxHelpers.requests(this);
                var data = {
                    certificates: [{course_id: 'xyz_test', mode: 'honor'}],
                    queried_features: ['course_id', 'mode'],
                    feature_names: {course_id: 'Course ID', mode: ' Mode'}
                };

                dataDownloadCertificates.$list_issued_certificate_table_btn.click();
                AjaxHelpers.expectJsonRequest(requests, 'POST', url);

                // Simulate a success response from the server
                AjaxHelpers.respondWithJson(requests, data);
                expect(dataDownloadCertificates.$certificate_display_table.html()
                    .indexOf('Course ID') !== -1).toBe(true);
                expect(dataDownloadCertificates.$certificate_display_table.html()
                    .indexOf('Mode') !== -1).toBe(true);
                expect(dataDownloadCertificates.$certificate_display_table.html()
                    .indexOf('xyz_test') !== -1).toBe(true);
                expect(dataDownloadCertificates.$certificate_display_table.html()
                    .indexOf('honor') !== -1).toBe(true);
            });

            it('show error on failure callback', function() {
                // Spy on AJAX requests
                var requests = AjaxHelpers.requests(this);

                dataDownloadCertificates.$list_issued_certificate_table_btn.click();
                // Simulate a error response from the server
                AjaxHelpers.respondWithError(requests);
                expect(dataDownloadCertificates.$certificates_request_response_error.text())
                    .toEqual('Error getting issued certificates list.');
            });

            it('error should be clear from UI on success callback', function() {
                var requests = AjaxHelpers.requests(this);
                dataDownloadCertificates.$list_issued_certificate_table_btn.click();

                // Simulate a error response from the server
                AjaxHelpers.respondWithError(requests);
                expect(dataDownloadCertificates.$certificates_request_response_error.text())
                    .toEqual('Error getting issued certificates list.');

                // Simulate a success response from the server
                dataDownloadCertificates.$list_issued_certificate_table_btn.click();
                AjaxHelpers.expectJsonRequest(requests, 'POST', url);

                expect(dataDownloadCertificates.$certificates_request_response_error.text())
                    .not.toEqual('Error getting issued certificates list');
            });
        });
    });
