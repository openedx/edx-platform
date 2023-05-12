/* eslint-disable vars-on-top */
// eslint-disable-next-line no-undef
define(
    [
        'gettext',
        'backbone',
        'jquery',
        'underscore',
        'edx-ui-toolkit/js/pagination/paging-collection',
        'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'common/js/spec_helpers/template_helpers',
        'js/spec/student_account/helpers',
        'learner_profile/js/spec_helpers/helpers',
        'js/views/fields',
        'js/student_account/models/user_account_model',
        'js/student_account/models/user_preferences_model',
        'learner_profile/js/views/learner_profile_fields',
        'learner_profile/js/views/learner_profile_view',
        'learner_profile/js/views/badge_list_container',
        'js/student_account/views/account_settings_fields',
        'js/views/message_banner'
    ],
    function(gettext, Backbone, $, _, PagingCollection, AjaxHelpers, TemplateHelpers, Helpers, LearnerProfileHelpers,
        FieldViews, UserAccountModel, AccountPreferencesModel, LearnerProfileFields, LearnerProfileView,
        BadgeListContainer, AccountSettingsFieldViews, MessageBannerView) {
        'use strict';

        describe('edx.user.LearnerProfileView', function() {
            // eslint-disable-next-line no-var
            var createLearnerProfileView = function(ownProfile, accountPrivacy, profileIsPublic) {
                // eslint-disable-next-line no-var
                var accountSettingsModel = new UserAccountModel();
                accountSettingsModel.set(Helpers.createAccountSettingsData());
                accountSettingsModel.set({profile_is_public: profileIsPublic});
                accountSettingsModel.set({profile_image: Helpers.PROFILE_IMAGE});

                // eslint-disable-next-line no-var
                var accountPreferencesModel = new AccountPreferencesModel();
                accountPreferencesModel.set({account_privacy: accountPrivacy});

                accountPreferencesModel.url = Helpers.USER_PREFERENCES_API_URL;

                // eslint-disable-next-line no-var
                var editable = ownProfile ? 'toggle' : 'never';

                // eslint-disable-next-line no-var
                var accountPrivacyFieldView = new LearnerProfileFields.AccountPrivacyFieldView({
                    model: accountPreferencesModel,
                    required: true,
                    editable: 'always',
                    showMessages: false,
                    title: 'edX learners can see my:',
                    valueAttribute: 'account_privacy',
                    options: [
                        ['all_users', 'Full Profile'],
                        ['private', 'Limited Profile']
                    ],
                    helpMessage: '',
                    accountSettingsPageUrl: '/account/settings/'
                });

                // eslint-disable-next-line no-var
                var messageView = new MessageBannerView({
                    el: $('.message-banner')
                });

                // eslint-disable-next-line no-var
                var profileImageFieldView = new LearnerProfileFields.ProfileImageFieldView({
                    model: accountSettingsModel,
                    valueAttribute: 'profile_image',
                    editable: editable,
                    messageView: messageView,
                    imageMaxBytes: Helpers.IMAGE_MAX_BYTES,
                    imageMinBytes: Helpers.IMAGE_MIN_BYTES,
                    imageUploadUrl: Helpers.IMAGE_UPLOAD_API_URL,
                    imageRemoveUrl: Helpers.IMAGE_REMOVE_API_URL
                });

                // eslint-disable-next-line no-var
                var usernameFieldView = new FieldViews.ReadonlyFieldView({
                    model: accountSettingsModel,
                    valueAttribute: 'username',
                    helpMessage: ''
                });

                // eslint-disable-next-line no-var
                var nameFieldView = new FieldViews.ReadonlyFieldView({
                    model: accountSettingsModel,
                    valueAttribute: 'name',
                    helpMessage: ''
                });

                // eslint-disable-next-line no-var
                var sectionOneFieldViews = [
                    new LearnerProfileFields.SocialLinkIconsView({
                        model: accountSettingsModel,
                        socialPlatforms: Helpers.SOCIAL_PLATFORMS,
                        ownProfile: true
                    }),

                    new FieldViews.DropdownFieldView({
                        title: gettext('Location'),
                        model: accountSettingsModel,
                        required: false,
                        editable: editable,
                        showMessages: false,
                        placeholderValue: '',
                        valueAttribute: 'country',
                        options: Helpers.FIELD_OPTIONS,
                        helpMessage: ''
                    }),

                    new AccountSettingsFieldViews.LanguageProficienciesFieldView({
                        title: gettext('Language'),
                        model: accountSettingsModel,
                        required: false,
                        editable: editable,
                        showMessages: false,
                        placeholderValue: 'Add language',
                        valueAttribute: 'language_proficiencies',
                        options: Helpers.FIELD_OPTIONS,
                        helpMessage: ''
                    }),

                    new FieldViews.DateFieldView({
                        model: accountSettingsModel,
                        valueAttribute: 'date_joined',
                        helpMessage: ''
                    })
                ];

                // eslint-disable-next-line no-var
                var sectionTwoFieldViews = [
                    new FieldViews.TextareaFieldView({
                        model: accountSettingsModel,
                        editable: editable,
                        showMessages: false,
                        title: 'About me',
                        placeholderValue: 'Tell other edX learners a little about yourself: where you live, '
                            + "what your interests are, why you're taking courses on edX, or what you hope to learn.",
                        valueAttribute: 'bio',
                        helpMessage: '',
                        messagePosition: 'header'
                    })
                ];

                // eslint-disable-next-line no-var
                var badgeCollection = new PagingCollection();
                badgeCollection.url = Helpers.BADGES_API_URL;

                // eslint-disable-next-line no-var
                var badgeListContainer = new BadgeListContainer({
                    attributes: {class: 'badge-set-display'},
                    collection: badgeCollection,
                    find_courses_url: Helpers.FIND_COURSES_URL
                });

                return new LearnerProfileView(
                    {
                        el: $('.wrapper-profile'),
                        ownProfile: ownProfile,
                        hasPreferencesAccess: true,
                        accountSettingsModel: accountSettingsModel,
                        preferencesModel: accountPreferencesModel,
                        accountPrivacyFieldView: accountPrivacyFieldView,
                        usernameFieldView: usernameFieldView,
                        nameFieldView: nameFieldView,
                        profileImageFieldView: profileImageFieldView,
                        sectionOneFieldViews: sectionOneFieldViews,
                        sectionTwoFieldViews: sectionTwoFieldViews,
                        badgeListContainer: badgeListContainer
                    });
            };

            beforeEach(function() {
                loadFixtures('learner_profile/fixtures/learner_profile.html');
            });

            afterEach(function() {
                Backbone.history.stop();
            });

            it('shows loading error correctly', function() {
                // eslint-disable-next-line no-var
                var learnerProfileView = createLearnerProfileView(false, 'all_users');

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();
                learnerProfileView.showLoadingError();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, true);
            });

            it('renders all fields as expected for self with full access', function() {
                // eslint-disable-next-line no-var
                var learnerProfileView = createLearnerProfileView(true, 'all_users', true);

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                LearnerProfileHelpers.expectProfileSectionsAndFieldsToBeRendered(learnerProfileView);
            });

            it('renders all fields as expected for self with limited access', function() {
                // eslint-disable-next-line no-var
                var learnerProfileView = createLearnerProfileView(true, 'private', false);

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                LearnerProfileHelpers.expectLimitedProfileSectionsAndFieldsToBeRendered(learnerProfileView);
            });

            it('renders the fields as expected for others with full access', function() {
                // eslint-disable-next-line no-var
                var learnerProfileView = createLearnerProfileView(false, 'all_users', true);

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                LearnerProfileHelpers.expectProfileSectionsAndFieldsToBeRendered(learnerProfileView, true);
            });

            it('renders the fields as expected for others with limited access', function() {
                // eslint-disable-next-line no-var
                var learnerProfileView = createLearnerProfileView(false, 'private', false);

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                LearnerProfileHelpers.expectLimitedProfileSectionsAndFieldsToBeRendered(learnerProfileView, true);
            });

            it("renders an error if the badges can't be fetched", function() {
                // eslint-disable-next-line no-var
                var learnerProfileView = createLearnerProfileView(false, 'all_users', true);
                learnerProfileView.options.accountSettingsModel.set({accomplishments_shared: true});
                // eslint-disable-next-line no-var
                var requests = AjaxHelpers.requests(this);

                learnerProfileView.render();

                LearnerProfileHelpers.breakBadgeLoading(learnerProfileView, requests);
                LearnerProfileHelpers.expectBadgeLoadingErrorIsRendered(learnerProfileView);
            });
        });
    });
