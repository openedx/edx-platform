define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/spec/student_account/helpers',
        'js/spec/student_profile/helpers',
        'js/views/fields',
        'js/student_account/models/user_account_model',
        'js/student_account/models/user_preferences_model',
        'js/student_profile/views/learner_profile_view',
        'js/student_profile/views/learner_profile_fields',
        'js/student_profile/views/learner_profile_factory',
        'js/views/message_banner'
        ],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, Helpers, LearnerProfileHelpers, FieldViews,
              UserAccountModel, UserPreferencesModel, LearnerProfileView, LearnerProfileFields, LearnerProfilePage) {
        'use strict';

        describe("edx.user.LearnerProfileFactory", function () {

            var requests;

            beforeEach(function () {
                loadFixtures('js/fixtures/student_profile/student_profile.html');
                TemplateHelpers.installTemplate('templates/fields/field_readonly');
                TemplateHelpers.installTemplate('templates/fields/field_dropdown');
                TemplateHelpers.installTemplate('templates/fields/field_textarea');
                TemplateHelpers.installTemplate('templates/fields/field_image');
                TemplateHelpers.installTemplate('templates/fields/message_banner');
                TemplateHelpers.installTemplate('templates/student_profile/learner_profile');
            });

            var createProfilePage = function(ownProfile) {
                return new LearnerProfilePage({
                    'accounts_api_url': Helpers.USER_ACCOUNTS_API_URL,
                    'preferences_api_url': Helpers.USER_PREFERENCES_API_URL,
                    'own_profile': ownProfile,
                    'account_settings_page_url': Helpers.USER_ACCOUNTS_API_URL,
                    'country_options': Helpers.FIELD_OPTIONS,
                    'language_options': Helpers.FIELD_OPTIONS,
                    'has_preferences_access': true,
                    'profile_image_max_bytes': Helpers.IMAGE_MAX_BYTES,
                    'profile_image_min_bytes': Helpers.IMAGE_MIN_BYTES,
                    'profile_image_upload_url': Helpers.IMAGE_UPLOAD_API_URL,
                    'profile_image_remove_url': Helpers.IMAGE_REMOVE_API_URL,
                    'default_visibility': 'all_users'
                });
            };

            it("show loading error when UserAccountModel fails to load", function() {

                requests = AjaxHelpers.requests(this);

                var context = createProfilePage(true),
                    learnerProfileView = context.learnerProfileView;

                var userAccountRequest = requests[0];
                expect(userAccountRequest.method).toBe('GET');
                expect(userAccountRequest.url).toBe(Helpers.USER_ACCOUNTS_API_URL);

                AjaxHelpers.respondWithError(requests, 500);

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, false);
                LearnerProfileHelpers.expectProfileSectionsNotToBeRendered(learnerProfileView);
            });

            it("shows loading error when UserPreferencesModel fails to load", function() {

                requests = AjaxHelpers.requests(this);

                var context = createProfilePage(true),
                    learnerProfileView = context.learnerProfileView;

                var userAccountRequest = requests[0];
                expect(userAccountRequest.method).toBe('GET');
                expect(userAccountRequest.url).toBe(Helpers.USER_ACCOUNTS_API_URL);

                AjaxHelpers.respondWithJson(requests, Helpers.createAccountSettingsData());
                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                LearnerProfileHelpers.expectProfileSectionsNotToBeRendered(learnerProfileView);

                var userPreferencesRequest = requests[1];
                expect(userPreferencesRequest.method).toBe('GET');
                expect(userPreferencesRequest.url).toBe(Helpers.USER_PREFERENCES_API_URL);

                AjaxHelpers.respondWithError(requests, 500);
                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, false);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, true);
                LearnerProfileHelpers.expectProfileSectionsNotToBeRendered(learnerProfileView);
            });

            it("renders the full profile after models are successfully fetched", function() {

                requests = AjaxHelpers.requests(this);

                var context = createProfilePage(true),
                    learnerProfileView = context.learnerProfileView;

                AjaxHelpers.respondWithJson(requests, Helpers.createAccountSettingsData());
                AjaxHelpers.respondWithJson(requests, Helpers.createUserPreferencesData());

                // sets the profile for full view.
                context.accountPreferencesModel.set({account_privacy: 'all_users'});
                LearnerProfileHelpers.expectProfileSectionsAndFieldsToBeRendered(learnerProfileView, false);
            });

            it("renders the limited profile for undefined 'year_of_birth'", function() {

                requests = AjaxHelpers.requests(this);

                var context = createProfilePage(true),
                    learnerProfileView = context.learnerProfileView;

                AjaxHelpers.respondWithJson(requests, Helpers.createAccountSettingsData({
                    year_of_birth: '',
                    requires_parental_consent: true
                }));
                AjaxHelpers.respondWithJson(requests, Helpers.createUserPreferencesData());

                LearnerProfileHelpers.expectLimitedProfileSectionsAndFieldsToBeRendered(learnerProfileView);
            });

            it("renders the limited profile for under 13 users", function() {

                requests = AjaxHelpers.requests(this);

                var context = createProfilePage(true),
                    learnerProfileView = context.learnerProfileView;

                AjaxHelpers.respondWithJson(requests, Helpers.createAccountSettingsData({
                    year_of_birth: new Date().getFullYear() - 10,
                    requires_parental_consent: true
                }));
                AjaxHelpers.respondWithJson(requests, Helpers.createUserPreferencesData());

                LearnerProfileHelpers.expectLimitedProfileSectionsAndFieldsToBeRendered(learnerProfileView);
            });
        });
    });
