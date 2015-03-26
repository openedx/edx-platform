;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone',
        'js/student_account/models/user_account_model',
        'js/student_account/models/user_preferences_model',
        'js/views/fields',
        'js/student_profile/views/learner_profile_fields',
        'js/student_profile/views/learner_profile_view'
    ], function (gettext, $, _, Backbone, AccountSettingsModel, AccountPreferencesModel, FieldsView,
                 LearnerProfileFieldsView, LearnerProfileView) {

        return function (options) {

            var learnerProfileElement = $('.wrapper-profile');

            var accountPreferencesModel = new AccountPreferencesModel();
            accountPreferencesModel.url = options['preferences_api_url'];

            var accountSettingsModel = new AccountSettingsModel({
                'default_public_account_fields': options['default_public_account_fields']
            });
            accountSettingsModel.url = options['accounts_api_url'];

            var editable = options['own_profile'] ? 'toggle' : 'never';

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
                accountSettingsPageUrl: options['account_settings_page_url']
            });

            var usernameFieldView = new FieldsView.ReadonlyFieldView({
                    model: accountSettingsModel,
                    valueAttribute: "username",
                    helpMessage: ""
            });

            var sectionOneFieldViews = [
                usernameFieldView,
                new FieldsView.DropdownFieldView({
                    model: accountSettingsModel,
                    required: true,
                    editable: editable,
                    showMessages: false,
                    iconName: 'fa-map-marker',
                    placeholderValue: gettext('Add country'),
                    valueAttribute: "country",
                    options: options['country_options'],
                    helpMessage: ''
                }),
                new FieldsView.DropdownFieldView({
                    model: accountSettingsModel,
                    required: false,
                    editable: editable,
                    showMessages: false,
                    iconName: 'fa-comment fa-flip-horizontal',
                    placeholderValue: gettext('Add language'),
                    valueAttribute: "language",
                    options: options['language_options'],
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
                own_profile: options['own_profile'],
                has_preferences_access: options['has_preferences_access'],
                accountSettingsModel: accountSettingsModel,
                preferencesModel: accountPreferencesModel,
                accountPrivacyFieldView: accountPrivacyFieldView,
                usernameFieldView: usernameFieldView,
                sectionOneFieldViews: sectionOneFieldViews,
                sectionTwoFieldViews: sectionTwoFieldViews
            });

            var showLoadingError = function () {
                learnerProfileView.showLoadingError();
            };

            var renderLearnerProfileView = function() {
                learnerProfileView.render();
            };

            accountSettingsModel.fetch({
                success: function () {
                    if (options['has_preferences_access']) {
                        accountPreferencesModel.fetch({
                            success: renderLearnerProfileView,
                            error: showLoadingError
                        });
                    }
                    else {
                        renderLearnerProfileView();
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
    })
}).call(this, define || RequireJS.define);
