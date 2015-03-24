define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/spec/student_account/helpers',
        'js/student_account/views/account_settings_fields',
        'js/student_account/models/user_account_model',
        'js/student_account/models/user_preferences_model',
        'js/student_profile/views/learner_profile_view',
        'js/student_profile/views/learner_profile_factory'
        ],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, Helpers, FieldViews, UserAccountModel, UserPreferencesModel,
              LearnerProfileView, LearnerProfilePage) {
        'use strict';

        describe("edx.user.LearnerProfileFactory", function () {


            var requests;

            beforeEach(function () {
                setFixtures('<div class="wrapper-profile"></div>');
                TemplateHelpers.installTemplate('templates/fields/field_readonly');
                TemplateHelpers.installTemplate('templates/fields/field_dropdown');
                TemplateHelpers.installTemplate('templates/fields/field_textarea');
                TemplateHelpers.installTemplate('templates/student_profile/learner_profile');
            });

            it("show loading error when UserAccountModel fails to load", function() {

                requests = AjaxHelpers.requests(this);

                var context = LearnerProfilePage({
                    'accounts_api_url': Helpers.USER_ACCOUNTS_API_URL,
                    'preferences_api_url': Helpers.USER_PREFERENCES_API_URL,
                    'own_profile': true,
                    'account_settings_page_url': Helpers.USER_ACCOUNTS_API_URL,
                    'country_options': Helpers.FIELD_OPTIONS,
                    'language_options': Helpers.FIELD_OPTIONS,
                    'has_preferences_access': true
                });

                var learnerProfileView = context.LearnerProfileView;

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(learnerProfileView);

                var request = requests[0];
                expect(request.method).toBe('GET');
                expect(request.url).toBe(Helpers.USER_ACCOUNTS_API_URL);

                AjaxHelpers.respondWithError(requests, 500);
                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, false);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, true);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(learnerProfileView);
            });


            it("shows loading error when UserPreferencesModel fails to load", function() {

                requests = AjaxHelpers.requests(this);

                var context = LearnerProfilePage({
                    'accounts_api_url': Helpers.USER_ACCOUNTS_API_URL,
                    'preferences_api_url': Helpers.USER_PREFERENCES_API_URL,
                    'own_profile': true,
                    'account_settings_page_url': Helpers.USER_ACCOUNTS_API_URL,
                    'country_options': Helpers.FIELD_OPTIONS,
                    'language_options': Helpers.FIELD_OPTIONS,
                    'has_preferences_access': true
                });
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

                var context = LearnerProfilePage({
                    'accounts_api_url': Helpers.USER_ACCOUNTS_API_URL,
                    'preferences_api_url': Helpers.USER_PREFERENCES_API_URL,
                    'own_profile': true,
                    'account_settings_page_url': Helpers.USER_ACCOUNTS_API_URL,
                    'country_options': Helpers.FIELD_OPTIONS,
                    'language_options': Helpers.FIELD_OPTIONS,
                    'has_preferences_access': true
                });

                var learnerProfileView = context.accountSettingsView;

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(learnerProfileView);

                AjaxHelpers.respondWithJson(requests, Helpers.USER_ACCOUNTS_DATA);
                AjaxHelpers.respondWithJson(requests, Helpers.USER_PREFERENCES_DATA);

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, false);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                Helpers.expectSettingsSectionsAndFieldsToBeRendered(learnerProfileView)
            });

        });
    });
