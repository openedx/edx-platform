;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone', 'logger',
        'js/views/fields',
        'js/student_account/models/user_account_model',
        'js/student_account/models/user_preferences_model',
        'js/student_account/views/account_settings_fields',
        'js/student_account/views/account_settings_view'
    ], function (gettext, $, _, Backbone, Logger, FieldViews, UserAccountModel, UserPreferencesModel,
                 AccountSettingsFieldViews, AccountSettingsView) {

        return function (fieldsData, authData, userAccountsApiUrl, userPreferencesApiUrl, accountUserId) {

            var accountSettingsElement = $('.wrapper-account-settings');

            var userAccountModel = new UserAccountModel();
            userAccountModel.url = userAccountsApiUrl;

            var userPreferencesModel = new UserPreferencesModel();
            userPreferencesModel.url = userPreferencesApiUrl;

            var sectionsData = [
                 {
                    title: gettext('Basic Account Information (required)'),
                    fields: [
                        {
                            view: new FieldViews.ReadonlyFieldView({
                                model: userAccountModel,
                                title: gettext('Username'),
                                valueAttribute: 'username',
                                helpMessage: gettext('The name that identifies you on the edX site. You cannot change your username.')
                            })
                        },
                        {
                            view: new FieldViews.TextFieldView({
                                model: userAccountModel,
                                title: gettext('Full Name'),
                                valueAttribute: 'name',
                                helpMessage: gettext('The name that appears on your edX certificates. Other learners never see your full name.')
                            })
                        },
                        {
                            view: new AccountSettingsFieldViews.EmailFieldView({
                                model: userAccountModel,
                                title: gettext('Email Address'),
                                valueAttribute: 'email',
                                helpMessage: gettext('The email address you use to sign in to edX. Communications from edX and your courses are sent to this address.')
                            })
                        },
                        {
                            view: new AccountSettingsFieldViews.PasswordFieldView({
                                model: userAccountModel,
                                title: gettext('Password'),
                                screenReaderTitle: gettext('Reset your Password'),
                                valueAttribute: 'password',
                                emailAttribute: 'email',
                                linkTitle: gettext('Reset Password'),
                                linkHref: fieldsData.password.url,
                                helpMessage: gettext('When you click "Reset Password", a message will be sent to your email address. Click the link in the message to reset your password.')
                            })
                        },
                        {
                            view: new AccountSettingsFieldViews.LanguagePreferenceFieldView({
                                model: userPreferencesModel,
                                title: gettext('Language'),
                                valueAttribute: 'pref-lang',
                                required: true,
                                refreshPageOnSave: true,
                                helpMessage:
                                    gettext('The language used for the edX site. The site is currently available in a limited number of languages.'),
                                options: fieldsData.language.options
                            })
                        },
                        {
                            view: new FieldViews.DropdownFieldView({
                                model: userAccountModel,
                                required: true,
                                title: gettext('Country or Region'),
                                valueAttribute: 'country',
                                options: fieldsData['country']['options']
                            })
                        }
                    ]
                },
                {
                    title: gettext('Additional Information (optional)'),
                    fields: [
                        {
                            view: new FieldViews.DropdownFieldView({
                                model: userAccountModel,
                                title: gettext('Education Completed'),
                                valueAttribute: 'level_of_education',
                                options: fieldsData.level_of_education.options
                            })
                        },
                        {
                            view: new FieldViews.DropdownFieldView({
                                model: userAccountModel,
                                title: gettext('Gender'),
                                valueAttribute: 'gender',
                                options: fieldsData.gender.options
                            })
                        },
                        {
                            view: new FieldViews.DropdownFieldView({
                                model: userAccountModel,
                                title: gettext('Year of Birth'),
                                valueAttribute: 'year_of_birth',
                                options: fieldsData['year_of_birth']['options']
                            })
                        },
                        {
                            view: new AccountSettingsFieldViews.LanguageProficienciesFieldView({
                                model: userAccountModel,
                                title: gettext('Preferred Language'),
                                valueAttribute: 'language_proficiencies',
                                options: fieldsData.preferred_language.options
                            })
                        }
                    ]
                }
            ];

            if (_.isArray(authData.providers)) {
                var accountsSectionData = {
                    title: gettext('Connected Accounts'),
                    fields: _.map(authData.providers, function(provider) {
                        return {
                            'view': new AccountSettingsFieldViews.AuthFieldView({
                                title: provider.name,
                                screenReaderTitle: interpolate_text(
                                    gettext("Connect your {accountName} account"), {accountName: provider['name']}
                                ),
                                valueAttribute: 'auth-' + provider.name.toLowerCase(),
                                helpMessage: '',
                                connected: provider.connected,
                                connectUrl: provider.connect_url,
                                disconnectUrl: provider.disconnect_url
                            })
                        };
                    })
                };
                sectionsData.push(accountsSectionData);
            }

            var accountSettingsView = new AccountSettingsView({
                model: userAccountModel,
                accountUserId: accountUserId,
                el: accountSettingsElement,
                sectionsData: sectionsData
            });

            accountSettingsView.render();

            var showLoadingError = function () {
                accountSettingsView.showLoadingError();
            };

            var showAccountFields = function () {
                // Record that the account settings page was viewed.
                Logger.log('edx.user.settings.viewed', {
                    page: "account",
                    visibility: null,
                    user_id: accountUserId
                });

                // Render the fields
                accountSettingsView.renderFields();
            };

            userAccountModel.fetch({
                success: function () {
                    // Fetch the user preferences model
                    userPreferencesModel.fetch({
                        success: showAccountFields,
                        error: showLoadingError
                    });
                },
                error: showLoadingError
            });

            return {
                userAccountModel: userAccountModel,
                userPreferencesModel: userPreferencesModel,
                accountSettingsView: accountSettingsView
            };
        };
    });
}).call(this, define || RequireJS.define);
