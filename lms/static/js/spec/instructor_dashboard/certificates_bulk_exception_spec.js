define([
        'jquery',
        'js/certificates/views/certificate_bulk_whitelist'
    ],
    function($, CertificateBulkWhiteListView) {
        'use strict';
        describe("certificate bulk exceptions generation", function() {

            var certificate_bulk_exception_url = 'test/url/';
            var SELECTORS = {
                upload_csv_button: ".upload-csv-button",
                bulk_white_list_exception_form: "form#bulk-white-list-exception-form",
                bulk_exception_results: ".bulk-exception-results"
            };
            beforeEach(function() {
                setFixtures();
                var fixture = readFixtures(
                    "templates/instructor/instructor_dashboard_2/certificate-bulk-white-list.underscore"
                );

                setFixtures(
                    "<script type='text/template' id='certificate-bulk-white-list-tpl'>" + fixture + "</script>" +
                    "<div class='bulk-white-list-exception'></div>"
                );

                this.view = new CertificateBulkWhiteListView({
                    bulk_exception_url: certificate_bulk_exception_url
                });
                this.view.render();
            });

            it('bind the ajax call and the result will be success', function() {
                var submitCallback;
                spyOn($, "ajax").andCallFake(function(params) {
                    params.success({
                        row_errors: {},
                        general_errors: [],
                        success: ["user test in row# 1"]
                    });
                    return {
                        always: function() {}
                    };
                });
                submitCallback = jasmine.createSpy().andReturn();
                this.view.$el.find(SELECTORS.bulk_white_list_exception_form).submit(submitCallback);
                this.view.$el.find(SELECTORS.upload_csv_button).click();
                expect($(SELECTORS.bulk_exception_results).text()).toContain('1 learner is successfully added to the ' +
                    'exception list');
            });

            it('bind the ajax call and the result will be general error', function() {
                var submitCallback;
                spyOn($, "ajax").andCallFake(function(params) {
                    params.success({
                        row_errors: {},
                        general_errors: ["File is not attached."],
                        success: []
                    });
                    return {
                        always: function() {}
                    };
                });
                submitCallback = jasmine.createSpy().andReturn();
                this.view.$el.find(SELECTORS.bulk_white_list_exception_form).submit(submitCallback);
                this.view.$el.find(SELECTORS.upload_csv_button).click();
                expect($(SELECTORS.bulk_exception_results).text()).toContain('File is not attached.');
            });

            it('bind the ajax call and the result will be singular form of row errors', function() {
                var submitCallback;
                spyOn($, "ajax").andCallFake(function(params) {
                    params.success({
                        general_errors: [],
                        row_errors: {
                            data_format_error: ['user 1 in row# 1'],
                            user_not_exist: ['user 2 in row# 2'],
                            user_already_white_listed: ['user 3 in row# 3'],
                            user_not_enrolled: ['user 4 in row# 4']
                        },
                        success: []
                    });
                    return {
                        always: function() {}
                    };
                });
                submitCallback = jasmine.createSpy().andReturn();
                this.view.$el.find(SELECTORS.bulk_white_list_exception_form).submit(submitCallback);
                this.view.$el.find(SELECTORS.upload_csv_button).click();
                expect($(SELECTORS.bulk_exception_results).text()).toContain('1 record is not in correct format');
                expect($(SELECTORS.bulk_exception_results).text()).toContain('1 learner does not exist in LMS');
                expect($(SELECTORS.bulk_exception_results).text()).toContain('1 learner is already white listed');
                expect($(SELECTORS.bulk_exception_results).text()).toContain('1 learner is not enrolled in course');

            });

            it('bind the ajax call and the result will be plural form of row errors', function() {
                var submitCallback;
                spyOn($, "ajax").andCallFake(function(params) {
                    params.success({
                        general_errors: [],
                        row_errors: {
                            data_format_error: ['user 1 in row# 1', 'user 1 in row# 1'],
                            user_not_exist: ['user 2 in row# 2', 'user 2 in row# 2'],
                            user_already_white_listed: ['user 3 in row# 3', 'user 3 in row# 3'],
                            user_not_enrolled: ['user 4 in row# 4', 'user 4 in row# 4']
                        },
                        success: []
                    });
                    return {
                        always: function() {}
                    };
                });
                submitCallback = jasmine.createSpy().andReturn();
                this.view.$el.find(SELECTORS.bulk_white_list_exception_form).submit(submitCallback);
                this.view.$el.find(SELECTORS.upload_csv_button).click();
                expect($(SELECTORS.bulk_exception_results).text()).toContain('2 records are not in correct format');
                expect($(SELECTORS.bulk_exception_results).text()).toContain('2 learners do not exist in LMS');
                expect($(SELECTORS.bulk_exception_results).text()).toContain('2 learners are already white listed');
                expect($(SELECTORS.bulk_exception_results).text()).toContain('2 learners are not enrolled in course');

            });

            it('toggle message details', function() {
                var submitCallback;
                spyOn($, "ajax").andCallFake(function(params) {
                    params.success({
                        row_errors: {},
                        general_errors: [],
                        success: ["user test in row# 1"]
                    });
                    return {
                        always: function() {}
                    };
                });
                submitCallback = jasmine.createSpy().andReturn();
                this.view.$el.find(SELECTORS.bulk_white_list_exception_form).submit(submitCallback);
                this.view.$el.find(SELECTORS.upload_csv_button).click();
                expect(this.view.$el.find("div.message > .successfully-added")).toBeHidden();
                this.view.$el.find("a.arrow#successfully-added").trigger( "click" );
                expect(this.view.$el.find("div.message > .successfully-added")).toBeVisible();

            });

        });
    });
