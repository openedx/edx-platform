define(['backbone', 'jquery', 'underscore', 'common/js/spec_helpers/ajax_helpers', 'common/js/spec_helpers/template_helpers',
        'js/spec/student_account/helpers',
        'js/spec/student_profile/helpers',
        'js/views/fields',
        'js/student_account/models/user_account_model',
        'js/student_account/models/user_preferences_model',
        'js/student_profile/views/learner_profile_fields',
        'js/student_profile/views/learner_profile_view',
        'js/student_account/views/account_settings_fields',
        'js/views/message_banner'
       ],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, Helpers, LearnerProfileHelpers, FieldViews,
              UserAccountModel, AccountPreferencesModel, LearnerProfileFields, LearnerProfileView,
              AccountSettingsFieldViews, MessageBannerView) {
        'use strict';

        describe("edx.user.LearnerProfileView", function () {

            var createLearnerProfileView = function (ownProfile, accountPrivacy, profileIsPublic) {

                var accountSettingsModel = new UserAccountModel();
                accountSettingsModel.set(Helpers.createAccountSettingsData());
                accountSettingsModel.set({'profile_is_public': profileIsPublic});
                accountSettingsModel.set({'profile_image': Helpers.PROFILE_IMAGE});

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

                var messageView = new MessageBannerView({
                    el: $('.message-banner')
                });

                var profileImageFieldView = new LearnerProfileFields.ProfileImageFieldView({
                    model: accountSettingsModel,
                    valueAttribute: "profile_image",
                    editable: editable,
                    messageView: messageView,
                    imageMaxBytes: Helpers.IMAGE_MAX_BYTES,
                    imageMinBytes: Helpers.IMAGE_MIN_BYTES,
                    imageUploadUrl: Helpers.IMAGE_UPLOAD_API_URL,
                    imageRemoveUrl: Helpers.IMAGE_REMOVE_API_URL
                });

                var usernameFieldView = new FieldViews.ReadonlyFieldView({
                        model: accountSettingsModel,
                        valueAttribute: "username",
                        helpMessage: ""
                });

                var sectionOneFieldViews = [
                    new FieldViews.DropdownFieldView({
                        model: accountSettingsModel,
                        required: false,
                        editable: editable,
                        showMessages: false,
                        iconName: 'fa-map-marker',
                        placeholderValue: '',
                        valueAttribute: "country",
                        options: Helpers.FIELD_OPTIONS,
                        helpMessage: ''
                    }),

                    new AccountSettingsFieldViews.LanguageProficienciesFieldView({
                        model: accountSettingsModel,
                        required: false,
                        editable: editable,
                        showMessages: false,
                        iconName: 'fa-comment',
                        placeholderValue: 'Add language',
                        valueAttribute: "language_proficiencies",
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
                        placeholderValue: "Tell other edX learners a little about yourself: where you live, " +
                            "what your interests are, why you're taking courses on edX, or what you hope to learn.",
                        valueAttribute: "bio",
                        helpMessage: '',
                        messagePosition: 'header'
                    })
                ];

                return new LearnerProfileView(
                    {
                        el: $('.wrapper-profile'),
                        ownProfile: ownProfile,
                        hasPreferencesAccess: true,
                        accountSettingsModel: accountSettingsModel,
                        preferencesModel: accountPreferencesModel,
                        accountPrivacyFieldView: accountPrivacyFieldView,
                        usernameFieldView: usernameFieldView,
                        profileImageFieldView: profileImageFieldView,
                        sectionOneFieldViews: sectionOneFieldViews,
                        sectionTwoFieldViews: sectionTwoFieldViews
                    });
            };

            beforeEach(function () {
                loadFixtures('js/fixtures/student_profile/student_profile.html');
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
                LearnerProfileHelpers.expectProfileSectionsAndFieldsToBeRendered(learnerProfileView);
            });

            it("renders all fields as expected for self with limited access", function() {

                var learnerProfileView = createLearnerProfileView(true, 'private', false);

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                LearnerProfileHelpers.expectLimitedProfileSectionsAndFieldsToBeRendered(learnerProfileView);
            });

            it("renders the fields as expected for others with full access", function() {

                var learnerProfileView = createLearnerProfileView(false, 'all_users', true);

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                LearnerProfileHelpers.expectProfileSectionsAndFieldsToBeRendered(learnerProfileView, true);
            });

            it("renders the fields as expected for others with limited access", function() {

                var learnerProfileView = createLearnerProfileView(false, 'private', false);

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                LearnerProfileHelpers.expectLimitedProfileSectionsAndFieldsToBeRendered(learnerProfileView, true);
            });
        });
    });
