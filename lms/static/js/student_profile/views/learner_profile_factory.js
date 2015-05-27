;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone', 'logger',
        'js/student_account/models/user_account_model',
        'js/student_account/models/user_preferences_model',
        'js/views/fields',
        'js/student_profile/views/learner_profile_fields',
        'js/student_profile/views/learner_profile_view',
        'js/student_account/views/account_settings_fields',
        'js/views/message_banner'
    ], function (gettext, $, _, Backbone, Logger, AccountSettingsModel, AccountPreferencesModel, FieldsView,
                 LearnerProfileFieldsView, LearnerProfileView, AccountSettingsFieldViews, MessageBannerView) {

        return function (options) {

            var learnerProfileElement = $('.wrapper-profile');
            var defaultVisibility = options.default_visibility;
            var AccountPreferencesModelWithDefaults = AccountPreferencesModel.extend({
                defaults: {
                    account_privacy: defaultVisibility
                }
            });
            var accountPreferencesModel = new AccountPreferencesModelWithDefaults();
            accountPreferencesModel.url = options.preferences_api_url;

            var accountSettingsModel = new AccountSettingsModel({
                'default_public_account_fields': options.default_public_account_fields
            });
            accountSettingsModel.url = options.accounts_api_url;

            var editable = options.own_profile ? 'toggle' : 'never';

            var messageView = new MessageBannerView({
                el: $('.message-banner')
            });

            var accountPrivacyFieldView = new LearnerProfileFieldsView.AccountPrivacyFieldView({
                model: accountPreferencesModel,
                required: true,
                editable: 'always',
                showMessages: false,
                title: gettext('edX learners can see my:'),
                valueAttribute: "account_privacy",
                options: [
                    ['private', gettext('Limited Profile')],
                    ['all_users', gettext('Full Profile')]
                ],
                helpMessage: '',
                accountSettingsPageUrl: options.account_settings_page_url
            });

            var profileImageFieldView = new LearnerProfileFieldsView.ProfileImageFieldView({
                model: accountSettingsModel,
                valueAttribute: "profile_image",
                editable: editable === 'toggle',
                messageView: messageView,
                imageMaxBytes: options['profile_image_max_bytes'],
                imageMinBytes: options['profile_image_min_bytes'],
                imageUploadUrl: options['profile_image_upload_url'],
                imageRemoveUrl: options['profile_image_remove_url']
            });

            var usernameFieldView = new FieldsView.ReadonlyFieldView({
                    model: accountSettingsModel,
                    screenReaderTitle: gettext('Username'),
                    valueAttribute: "username",
                    helpMessage: ""
            });

            var sectionOneFieldViews = [
                new FieldsView.DropdownFieldView({
                    model: accountSettingsModel,
                    screenReaderTitle: gettext('Country'),
                    required: true,
                    editable: editable,
                    showMessages: false,
                    iconName: 'fa-map-marker',
                    placeholderValue: gettext('Add Country'),
                    valueAttribute: "country",
                    options: options.country_options,
                    helpMessage: ''
                }),
                new AccountSettingsFieldViews.LanguageProficienciesFieldView({
                    model: accountSettingsModel,
                    screenReaderTitle: gettext('Preferred Language'),
                    required: false,
                    editable: editable,
                    showMessages: false,
                    iconName: 'fa-comment',
                    placeholderValue: gettext('Add language'),
                    valueAttribute: "language_proficiencies",
                    options: options.language_options,
                    helpMessage: ''
                })
            ];

            var sectionTwoFieldViews = [
                new FieldsView.TextareaFieldView({
                    model: accountSettingsModel,
                    editable: editable,
                    showMessages: false,
                    title: gettext('About me'),
                    placeholderValue: gettext("Tell other edX learners a little about yourself: where you live, what your interests are, why you're taking courses on edX, or what you hope to learn."),
                    valueAttribute: "bio",
                    helpMessage: ''
                })
            ];

            var learnerProfileView = new LearnerProfileView({
                el: learnerProfileElement,
                ownProfile: options.own_profile,
                has_preferences_access: options.has_preferences_access,
                accountSettingsModel: accountSettingsModel,
                preferencesModel: accountPreferencesModel,
                accountPrivacyFieldView: accountPrivacyFieldView,
                profileImageFieldView: profileImageFieldView,
                usernameFieldView: usernameFieldView,
                sectionOneFieldViews: sectionOneFieldViews,
                sectionTwoFieldViews: sectionTwoFieldViews
            });

            var showLoadingError = function () {
                learnerProfileView.showLoadingError();
            };

            var getProfileVisibility = function() {
                if (options.has_preferences_access) {
                    return accountPreferencesModel.get('account_privacy');
                } else {
                    return accountSettingsModel.get('profile_is_public') ? 'all_users' : 'private';
                }
            };

            var showLearnerProfileView = function() {
                // Record that the profile page was viewed
                Logger.log('edx.user.settings.viewed', {
                    page: "profile",
                    visibility: getProfileVisibility(),
                    user_id: options.profile_user_id
                });

                // Render the view for the first time
                learnerProfileView.render();
            };

            accountSettingsModel.fetch({
                success: function () {
                    // Fetch the preferences model if the user has access
                    if (options.has_preferences_access) {
                        accountPreferencesModel.fetch({
                            success: function() {
                                if (accountSettingsModel.get('requires_parental_consent')) {
                                    accountPreferencesModel.set('account_privacy', 'private');
                                }
                                showLearnerProfileView();
                            },
                            error: showLoadingError
                        });
                    }
                    else {
                        showLearnerProfileView();
                    }
                },
                error: showLoadingError
            });

            return {
                accountSettingsModel: accountSettingsModel,
                accountPreferencesModel: accountPreferencesModel,
                learnerProfileView: learnerProfileView
            };
        };
    });
}).call(this, define || RequireJS.define);
