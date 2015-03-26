define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/spec/student_account/helpers',
        'js/views/fields',
        'js/student_account/models/user_account_model',
        'js/student_account/models/user_preferences_model',
        'js/student_profile/views/learner_profile_fields',
        'js/student_profile/views/learner_profile_view'
       ],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, Helpers, FieldViews, UserAccountModel,
                AccountPreferencesModel, LearnerProfileFields, LearnerProfileView) {
        'use strict';

        describe("edx.user.LearnerProfileView", function (options) {

            var createLearnerProfileView = function (ownProfile, accountPrivacy, profileIsPublic) {

                var accountSettingsModel = new UserAccountModel();
                accountSettingsModel.set(Helpers.USER_ACCOUNTS_DATA);
                accountSettingsModel.set({'profile_is_public': profileIsPublic});

                var accountPreferencesModel = new AccountPreferencesModel();
                accountPreferencesModel.set({account_privacy: accountPrivacy});

                accountPreferencesModel.url = Helpers.USER_PREFERENCES_API_URL;

                var editable = ownProfile ? 'toggle' : 'never';

                var accountPrivacyFieldView = new LearnerProfileFields.AccountPrivacyFieldView({
                    model: accountPreferencesModel,
                    required: true,
                    editable: 'always',
                    showMessages: false,
                    title: 'edX learners can see my:',
                    valueAttribute: "account_privacy",
                    options: [
                        ['all_users', 'Full Profile'],
                        ['private', 'Limited Profile']
                    ],
                    helpMessage: '',
                    accountSettingsPageUrl: '/account/settings/'
                });

                var usernameFieldView = new FieldViews.ReadonlyFieldView({
                        model: accountSettingsModel,
                        valueAttribute: "username",
                        helpMessage: ""
                });

                var sectionOneFieldViews = [
                    usernameFieldView,
                    new FieldViews.DropdownFieldView({
                        model: accountSettingsModel,
                        required: false,
                        editable: editable,
                        showMessages: false,
                        iconName: 'fa-map-marker',
                        placeholderValue: 'Add country',
                        valueAttribute: "country",
                        options: Helpers.FIELD_OPTIONS,
                        helpMessage: ''
                    }),

                    new FieldViews.DropdownFieldView({
                        model: accountSettingsModel,
                        required: false,
                        editable: editable,
                        showMessages: false,
                        iconName: 'fa-comment fa-flip-horizontal',
                        placeholderValue: 'Add language',
                        valueAttribute: "language",
                        options: Helpers.FIELD_OPTIONS,
                        helpMessage: ''
                    })
                ];

                var sectionTwoFieldViews = [
                    new FieldViews.TextareaFieldView({
                        model: accountSettingsModel,
                        editable: editable,
                        showMessages: false,
                        title: 'About me',
                        placeholderValue: "Tell other edX learners a little about yourself: where you live, what your interests are, why you're taking courses on edX, or what you hope to learn.",
                        valueAttribute: "bio",
                        helpMessage: ''
                    })
                ];

                return new LearnerProfileView(
                    {
                        el: $('.wrapper-profile'),
                        own_profile: ownProfile,
                        has_preferences_access: true,
                        accountSettingsModel: accountSettingsModel,
                        preferencesModel: accountPreferencesModel,
                        accountPrivacyFieldView: accountPrivacyFieldView,
                        usernameFieldView: usernameFieldView,
                        sectionOneFieldViews: sectionOneFieldViews,
                        sectionTwoFieldViews: sectionTwoFieldViews
                    });

            };

            beforeEach(function () {
                setFixtures('<div class="wrapper-profile"><div class="ui-loading-indicator"><p><span class="spin"><i class="icon fa fa-refresh"></i></span> <span class="copy">Loading</span></p></div><div class="ui-loading-error is-hidden"><i class="fa fa-exclamation-triangle message-error" aria-hidden=true></i><span class="copy">An error occurred. Please reload the page.</span></div></div>');
                TemplateHelpers.installTemplate('templates/fields/field_readonly');
                TemplateHelpers.installTemplate('templates/fields/field_dropdown');
                TemplateHelpers.installTemplate('templates/fields/field_textarea');
                TemplateHelpers.installTemplate('templates/student_profile/learner_profile');
            });

            it("shows loading error correctly", function() {

                var learnerProfileView = createLearnerProfileView(false, 'all_users');

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();
                learnerProfileView.showLoadingError();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, true);
            });

            it("renders all fields as expected for self with full access", function() {

                var learnerProfileView = createLearnerProfileView(true, 'all_users', true);

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                Helpers.expectProfileSectionsAndFieldsToBeRendered(learnerProfileView);
            });

            it("renders all fields as expected for self with limited access", function() {

                var learnerProfileView = createLearnerProfileView(true, 'private', false);

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                Helpers.expectLimitedProfileSectionsAndFieldsToBeRendered(learnerProfileView);
            });

            it("renders the fields as expected for others with full access", function() {

                var learnerProfileView = createLearnerProfileView(false, 'all_users', true);

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                Helpers.expectProfileSectionsAndFieldsToBeRendered(learnerProfileView, true)
            });

            it("renders the fields as expected for others with limited access", function() {

                var learnerProfileView = createLearnerProfileView(false, 'private', false);

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                Helpers.expectLimitedProfileSectionsAndFieldsToBeRendered(learnerProfileView, true);
            });
        });
    });
