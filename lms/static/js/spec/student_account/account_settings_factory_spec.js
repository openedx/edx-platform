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
            var FIELDS_DATA = {
                'country': {
                    'options': Helpers.FIELD_OPTIONS
                }, 'gender': {
                    'options': Helpers.FIELD_OPTIONS
                }, 'language': {
                    'options': Helpers.FIELD_OPTIONS
                }, 'level_of_education': {
                    'options': Helpers.FIELD_OPTIONS
                }, 'password': {
                    'url': '/password_reset'
                }, 'year_of_birth': {
                    'options': Helpers.FIELD_OPTIONS
                }, 'preferred_language': {
                    'options': Helpers.FIELD_OPTIONS
                }, 'time_zone': {
                    'options': Helpers.FIELD_OPTIONS
                }
            };

            var AUTH_DATA = {
                'providers': [
                    {
                        'id': 'oa2-network1',
                        'name': 'Network1',
                        'connected': true,
                        'accepts_logins': 'true',
                        'connect_url': 'yetanother1.com/auth/connect',
                        'disconnect_url': 'yetanother1.com/auth/disconnect'
                    },
                    {
                        'id': 'oa2-network2',
                        'name': 'Network2',
                        'connected': true,
                        'accepts_logins': 'true',
                        'connect_url': 'yetanother2.com/auth/connect',
                        'disconnect_url': 'yetanother2.com/auth/disconnect'
                    }
                ]
            };

            var createAccountSettingsPage = function() {
                var context = AccountSettingsPage(
                    FIELDS_DATA, [], AUTH_DATA, Helpers.USER_ACCOUNTS_API_URL, Helpers.USER_PREFERENCES_API_URL, 'edX'
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


            it('shows loading error when UserPreferencesModel fails to load', function() {
                requests = AjaxHelpers.requests(this);

                var accountSettingsView = createAccountSettingsPage();

                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, true);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(accountSettingsView);

                var request = requests[0];
                expect(request.method).toBe('GET');
                expect(request.url).toBe(Helpers.USER_ACCOUNTS_API_URL);

                AjaxHelpers.respondWithJson(requests, Helpers.createAccountSettingsData());
                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, true);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(accountSettingsView);

                request = requests[1];
                expect(request.method).toBe('GET');
                expect(request.url).toBe('/user_api/v1/preferences/time_zones/?country_code=1');
                AjaxHelpers.respondWithJson(requests, Helpers.TIME_ZONE_RESPONSE);

                request = requests[2];
                expect(request.method).toBe('GET');
                expect(request.url).toBe(Helpers.USER_PREFERENCES_API_URL);

                AjaxHelpers.respondWithError(requests, 500);
                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, false);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, true);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(accountSettingsView);
            });

            it('renders fields after the models are successfully fetched', function() {
                requests = AjaxHelpers.requests(this);

                var accountSettingsView = createAccountSettingsPage();

                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, true);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(accountSettingsView);

                AjaxHelpers.respondWithJson(requests, Helpers.createAccountSettingsData());
                AjaxHelpers.respondWithJson(requests, Helpers.TIME_ZONE_RESPONSE);
                AjaxHelpers.respondWithJson(requests, Helpers.createUserPreferencesData());

                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, false);
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
    });
