define(['backbone',
    'jquery',
    'underscore',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'common/js/spec_helpers/template_helpers',
    'js/spec/views/fields_helpers',
    'js/spec/student_account/helpers',
    'js/spec/student_account/account_settings_fields_helpers',
    'js/student_account/views/account_settings_factory',
    'js/student_account/views/account_settings_view'
],
    function(Backbone, $, _, AjaxHelpers, TemplateHelpers, FieldViewsSpecHelpers, Helpers,
              AccountSettingsFieldViewSpecHelpers, AccountSettingsPage) {
        'use strict';

        describe('edx.user.AccountSettingsFactory', function() {
            var createAccountSettingsPage = function() {
                var context = AccountSettingsPage(
                    Helpers.FIELDS_DATA,
                    false,
                    [],
                    Helpers.AUTH_DATA,
                    Helpers.PASSWORD_RESET_SUPPORT_LINK,
                    Helpers.USER_ACCOUNTS_API_URL,
                    Helpers.USER_PREFERENCES_API_URL,
                    1,
                    Helpers.PLATFORM_NAME,
                    Helpers.CONTACT_EMAIL,
                    true
                );
                return context.accountSettingsView;
            };

            var requests;

            beforeEach(function() {
                setFixtures('<div class="wrapper-account-settings"></div>');
            });

            it('shows loading error when UserAccountModel fails to load', function() {
                requests = AjaxHelpers.requests(this);

                var accountSettingsView = createAccountSettingsPage();

                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);

                var request = requests[0];
                expect(request.method).toBe('GET');
                expect(request.url).toBe(Helpers.USER_ACCOUNTS_API_URL);

                AjaxHelpers.respondWithError(requests, 500);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, true);
            });


            it('shows loading error when UserPreferencesModel fails to load', function() {
                requests = AjaxHelpers.requests(this);

                var accountSettingsView = createAccountSettingsPage();

                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);

                var request = requests[0];
                expect(request.method).toBe('GET');
                expect(request.url).toBe(Helpers.USER_ACCOUNTS_API_URL);

                AjaxHelpers.respondWithJson(requests, Helpers.createAccountSettingsData());
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);

                request = requests[1];
                expect(request.method).toBe('GET');
                expect(request.url).toBe('/user_api/v1/preferences/time_zones/?country_code=1');
                AjaxHelpers.respondWithJson(requests, Helpers.TIME_ZONE_RESPONSE);

                request = requests[2];
                expect(request.method).toBe('GET');
                expect(request.url).toBe(Helpers.USER_PREFERENCES_API_URL);

                AjaxHelpers.respondWithError(requests, 500);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, true);
            });

            it('renders fields after the models are successfully fetched', function() {
                requests = AjaxHelpers.requests(this);

                var accountSettingsView = createAccountSettingsPage();

                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);

                AjaxHelpers.respondWithJson(requests, Helpers.createAccountSettingsData());
                AjaxHelpers.respondWithJson(requests, Helpers.TIME_ZONE_RESPONSE);
                AjaxHelpers.respondWithJson(requests, Helpers.createUserPreferencesData());

                accountSettingsView.render();

                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsAndFieldsToBeRendered(accountSettingsView);
            });

            it('expects all fields to behave correctly', function() {
                var i, view;

                requests = AjaxHelpers.requests(this);

                var accountSettingsView = createAccountSettingsPage();

                AjaxHelpers.respondWithJson(requests, Helpers.createAccountSettingsData());
                AjaxHelpers.respondWithJson(requests, Helpers.TIME_ZONE_RESPONSE);
                AjaxHelpers.respondWithJson(requests, Helpers.createUserPreferencesData());
                AjaxHelpers.respondWithJson(requests, {});  // Page viewed analytics event

                var sectionsData = accountSettingsView.options.tabSections.aboutTabSections;

                expect(sectionsData[0].fields.length).toBe(7);

                var textFields = [sectionsData[0].fields[1], sectionsData[0].fields[2]];
                for (i = 0; i < textFields.length; i++) {
                    view = textFields[i].view;
                    FieldViewsSpecHelpers.verifyTextField(view, {
                        title: view.options.title,
                        valueAttribute: view.options.valueAttribute,
                        helpMessage: view.options.helpMessage,
                        validValue: 'My Name',
                        invalidValue1: '',
                        invalidValue2: '@',
                        validationError: 'Think again!',
                        defaultValue: ''
                    }, requests);
                }

                expect(sectionsData[1].fields.length).toBe(4);
                var dropdownFields = [
                    sectionsData[1].fields[0],
                    sectionsData[1].fields[1],
                    sectionsData[1].fields[2]
                ];
                _.each(dropdownFields, function(field) {
                    var view = field.view;
                    FieldViewsSpecHelpers.verifyDropDownField(view, {
                        title: view.options.title,
                        valueAttribute: view.options.valueAttribute,
                        helpMessage: '',
                        validValue: Helpers.FIELD_OPTIONS[1][0],
                        invalidValue1: Helpers.FIELD_OPTIONS[2][0],
                        invalidValue2: Helpers.FIELD_OPTIONS[3][0],
                        validationError: 'Nope, this will not do!',
                        defaultValue: null
                    }, requests);
                });
            });
        });

        describe('edx.user.AccountSettingsFactory', function() {
            var createEnterpriseLearnerAccountSettingsPage = function() {
                var context = AccountSettingsPage(
                    Helpers.FIELDS_DATA,
                    false,
                    [],
                    Helpers.AUTH_DATA,
                    Helpers.PASSWORD_RESET_SUPPORT_LINK,
                    Helpers.USER_ACCOUNTS_API_URL,
                    Helpers.USER_PREFERENCES_API_URL,
                    1,
                    Helpers.PLATFORM_NAME,
                    Helpers.CONTACT_EMAIL,
                    true,
                    '',

                    Helpers.SYNC_LEARNER_PROFILE_DATA,
                    Helpers.ENTERPRISE_NAME,
                    Helpers.ENTERPRISE_READ_ONLY_ACCOUNT_FIELDS,
                    Helpers.EDX_SUPPORT_URL
                );
                return context.accountSettingsView;
            };

            var requests;
            var accountInfoTab = {
                BASIC_ACCOUNT_INFORMATION: 0,
                ADDITIONAL_INFORMATION: 1
            };
            var basicAccountInfoFields = {
                USERNAME: 0,
                FULL_NAME: 1,
                EMAIL_ADDRESS: 2,
                PASSWORD: 3,
                LANGUAGE: 4,
                COUNTRY: 5,
                TIMEZONE: 6
            };
            var additionalInfoFields = {
                EDUCATION: 0,
                GENDER: 1,
                YEAR_OF_BIRTH: 2,
                PREFERRED_LANGUAGE: 3
            };

            beforeEach(function() {
                setFixtures('<div class="wrapper-account-settings"></div>');
            });

            it('shows loading error when UserAccountModel fails to load for enterprise learners', function() {
                var accountSettingsView, request;
                requests = AjaxHelpers.requests(this);

                accountSettingsView = createEnterpriseLearnerAccountSettingsPage();

                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);

                request = requests[0];
                expect(request.method).toBe('GET');
                expect(request.url).toBe(Helpers.USER_ACCOUNTS_API_URL);

                AjaxHelpers.respondWithError(requests, 500);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, true);
            });

            it('shows loading error when UserPreferencesModel fails to load for enterprise learners', function() {
                var accountSettingsView, request;
                requests = AjaxHelpers.requests(this);

                accountSettingsView = createEnterpriseLearnerAccountSettingsPage();

                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);

                request = requests[0];
                expect(request.method).toBe('GET');
                expect(request.url).toBe(Helpers.USER_ACCOUNTS_API_URL);

                AjaxHelpers.respondWithJson(requests, Helpers.createAccountSettingsData());
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);

                request = requests[1];
                expect(request.method).toBe('GET');
                expect(request.url).toBe('/user_api/v1/preferences/time_zones/?country_code=1');
                AjaxHelpers.respondWithJson(requests, Helpers.TIME_ZONE_RESPONSE);

                request = requests[2];
                expect(request.method).toBe('GET');
                expect(request.url).toBe(Helpers.USER_PREFERENCES_API_URL);

                AjaxHelpers.respondWithError(requests, 500);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, true);
            });

            it('renders fields after the models are successfully fetched for enterprise learners', function() {
                var accountSettingsView;
                requests = AjaxHelpers.requests(this);

                accountSettingsView = createEnterpriseLearnerAccountSettingsPage();

                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);

                AjaxHelpers.respondWithJson(requests, Helpers.createAccountSettingsData());
                AjaxHelpers.respondWithJson(requests, Helpers.TIME_ZONE_RESPONSE);
                AjaxHelpers.respondWithJson(requests, Helpers.createUserPreferencesData());

                accountSettingsView.render();

                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsAndFieldsToBeRenderedWithMessage(accountSettingsView);
            });

            it('expects all fields to behave correctly for enterprise learners', function() {
                var accountSettingsView, i, view, sectionsData, textFields, dropdownFields;
                requests = AjaxHelpers.requests(this);

                accountSettingsView = createEnterpriseLearnerAccountSettingsPage();

                AjaxHelpers.respondWithJson(requests, Helpers.createAccountSettingsData());
                AjaxHelpers.respondWithJson(requests, Helpers.TIME_ZONE_RESPONSE);
                AjaxHelpers.respondWithJson(requests, Helpers.createUserPreferencesData());
                AjaxHelpers.respondWithJson(requests, {});  // Page viewed analytics event

                sectionsData = accountSettingsView.options.tabSections.aboutTabSections;

                expect(sectionsData[accountInfoTab.BASIC_ACCOUNT_INFORMATION].fields.length).toBe(7);

                // Verify that username, name and email fields are readonly
                textFields = [
                    sectionsData[accountInfoTab.BASIC_ACCOUNT_INFORMATION].fields[basicAccountInfoFields.USERNAME],
                    sectionsData[accountInfoTab.BASIC_ACCOUNT_INFORMATION].fields[basicAccountInfoFields.FULL_NAME],
                    sectionsData[accountInfoTab.BASIC_ACCOUNT_INFORMATION].fields[basicAccountInfoFields.EMAIL_ADDRESS]
                ];
                for (i = 0; i < textFields.length; i++) {
                    view = textFields[i].view;

                    FieldViewsSpecHelpers.verifyReadonlyTextField(view, {
                        title: view.options.title,
                        valueAttribute: view.options.valueAttribute,
                        helpMessage: view.options.helpMessage,
                        validValue: 'My Name',
                        defaultValue: ''
                    }, requests);
                }

                // Verify un-editable country dropdown field
                view = sectionsData[
                    accountInfoTab.BASIC_ACCOUNT_INFORMATION
                ].fields[basicAccountInfoFields.COUNTRY].view;

                FieldViewsSpecHelpers.verifyReadonlyDropDownField(view, {
                    title: view.options.title,
                    valueAttribute: view.options.valueAttribute,
                    helpMessage: '',
                    validValue: Helpers.FIELD_OPTIONS[1][0],
                    editable: 'never',
                    defaultValue: null
                });

                expect(sectionsData[accountInfoTab.ADDITIONAL_INFORMATION].fields.length).toBe(4);
                dropdownFields = [
                    sectionsData[accountInfoTab.ADDITIONAL_INFORMATION].fields[additionalInfoFields.EDUCATION],
                    sectionsData[accountInfoTab.ADDITIONAL_INFORMATION].fields[additionalInfoFields.GENDER],
                    sectionsData[accountInfoTab.ADDITIONAL_INFORMATION].fields[additionalInfoFields.YEAR_OF_BIRTH]
                ];
                _.each(dropdownFields, function(field) {
                    view = field.view;
                    FieldViewsSpecHelpers.verifyDropDownField(view, {
                        title: view.options.title,
                        valueAttribute: view.options.valueAttribute,
                        helpMessage: '',
                        validValue: Helpers.FIELD_OPTIONS[1][0],    // dummy option for dropdown field
                        invalidValue1: Helpers.FIELD_OPTIONS[2][0], // dummy option for dropdown field
                        invalidValue2: Helpers.FIELD_OPTIONS[3][0], // dummy option for dropdown field
                        validationError: 'Nope, this will not do!',
                        defaultValue: null
                    }, requests);
                });
            });
        });
    });
