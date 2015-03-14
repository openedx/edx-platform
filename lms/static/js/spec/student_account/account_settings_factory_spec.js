define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/spec/student_account/helpers',
        'js/student_account/views/account_settings_fields',
        'js/student_account/models/user_account_model',
        'js/student_account/models/user_preferences_model',
        'js/student_account/views/account_settings_factory',
        'js/student_account/views/account_settings_view'
        ],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, Helpers, FieldViews, UserAccountModel, UserPreferencesModel,
              AccountSettingsPage, AccountSettingsView) {
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

            it("show loading error when UserAccountModel fails to load", function() {

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

        });
    });
