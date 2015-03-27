define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/spec/views/fields_helpers',
        'js/spec/student_account/helpers',
        'js/student_account/views/account_settings_factory',
        'js/student_account/views/account_settings_view'
        ],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, FieldViewsSpecHelpers, Helpers, AccountSettingsPage, AccountSettingsView) {
        'use strict';

        describe("edx.user.AccountSettingsFactory", function () {

            var FIELDS_DATA = {
                'country': {
                    'options': Helpers.FIELD_OPTIONS,
                }, 'gender': {
                    'options': Helpers.FIELD_OPTIONS,
                }, 'language': {
                    'options': Helpers.FIELD_OPTIONS,
                }, 'level_of_education': {
                    'options': Helpers.FIELD_OPTIONS,
                }, 'password': {
                    'url': '/password_reset',
                }, 'year_of_birth': {
                    'options': Helpers.FIELD_OPTIONS,
                }, 'preferred_language': {
                    'options': Helpers.FIELD_OPTIONS,
                }
            };

            var requests;

            beforeEach(function () {
                setFixtures('<div class="wrapper-account-settings"></div>');
                TemplateHelpers.installTemplate('templates/fields/field_readonly');
                TemplateHelpers.installTemplate('templates/fields/field_dropdown');
                TemplateHelpers.installTemplate('templates/fields/field_link');
                TemplateHelpers.installTemplate('templates/fields/field_text');
                TemplateHelpers.installTemplate('templates/student_account/account_settings');
            });

            it("shows loading error when UserAccountModel fails to load", function() {

                requests = AjaxHelpers.requests(this);

                var context = AccountSettingsPage(
                    FIELDS_DATA, Helpers.USER_ACCOUNTS_API_URL, Helpers.USER_PREFERENCES_API_URL
                );
                var accountSettingsView = context.accountSettingsView;

                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, true);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(accountSettingsView);

                var request = requests[0];
                expect(request.method).toBe('GET');
                expect(request.url).toBe(Helpers.USER_ACCOUNTS_API_URL);

                AjaxHelpers.respondWithError(requests, 500);
                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, false);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, true);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(accountSettingsView);
            });


            it("shows loading error when UserPreferencesModel fails to load", function() {

                requests = AjaxHelpers.requests(this);

                var context = AccountSettingsPage(
                    FIELDS_DATA, Helpers.USER_ACCOUNTS_API_URL, Helpers.USER_PREFERENCES_API_URL
                );
                var accountSettingsView = context.accountSettingsView;

                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, true);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(accountSettingsView);

                var request = requests[0];
                expect(request.method).toBe('GET');
                expect(request.url).toBe(Helpers.USER_ACCOUNTS_API_URL);

                AjaxHelpers.respondWithJson(requests, Helpers.USER_ACCOUNTS_DATA);
                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, true);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(accountSettingsView);

                var request = requests[1];
                expect(request.method).toBe('GET');
                expect(request.url).toBe(Helpers.USER_PREFERENCES_API_URL);

                AjaxHelpers.respondWithError(requests, 500);
                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, false);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, true);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(accountSettingsView);
            });

            it("renders fields after the models are successfully fetched", function() {

                requests = AjaxHelpers.requests(this);

                var context = AccountSettingsPage(
                    FIELDS_DATA, Helpers.USER_ACCOUNTS_API_URL, Helpers.USER_PREFERENCES_API_URL
                );
                var accountSettingsView = context.accountSettingsView;

                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, true);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(accountSettingsView);

                AjaxHelpers.respondWithJson(requests, Helpers.USER_ACCOUNTS_DATA);
                AjaxHelpers.respondWithJson(requests, Helpers.USER_PREFERENCES_DATA);

                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, false);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsAndFieldsToBeRendered(accountSettingsView)
            });

            it("expects all fields to behave correctly", function () {

                requests = AjaxHelpers.requests(this);

                var context = AccountSettingsPage(
                    FIELDS_DATA, Helpers.USER_ACCOUNTS_API_URL, Helpers.USER_PREFERENCES_API_URL
                );
                var accountSettingsView = context.accountSettingsView;

                AjaxHelpers.respondWithJson(requests, Helpers.USER_ACCOUNTS_DATA);
                AjaxHelpers.respondWithJson(requests, Helpers.USER_PREFERENCES_DATA);

                var sectionsData = accountSettingsView.options.sectionsData;

                expect(sectionsData[0].fields.length).toBe(5);

                var textFields = [sectionsData[0].fields[1], sectionsData[0].fields[2]];
                for (var i = 0; i < textFields ; i++) {

                    var view = textFields[i].view;
                    FieldViewsSpecHelpers.verifyTextField(view, {
                        title: view.options.title,
                        valueAttribute: view.options.valueAttribute,
                        helpMessage: view.options.helpMessage,
                        validValue: 'My Name',
                        invalidValue1: '',
                        invalidValue2: '@',
                        validationError: "Think again!"
                    }, requests);
                }

                expect(sectionsData[1].fields.length).toBe(5);
                for (var i = 0; i < 4; i++) {

                    var view = sectionsData[1].fields[i].view;
                    FieldViewsSpecHelpers.verifyDropDownField(view, {
                        title: view.options.title,
                        valueAttribute: view.options.valueAttribute,
                        helpMessage: '',
                        validValue: Helpers.FIELD_OPTIONS[0][0],
                        invalidValue1: Helpers.FIELD_OPTIONS[1][0],
                        invalidValue2: Helpers.FIELD_OPTIONS[2][0],
                        validationError: "Nope, this will not do!"
                    }, requests);
                }

            });
        });
    });
