;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone',
        'js/student_account/models/user_account_model',
        'js/student_account/models/user_preferences_model',
        'js/student_account/views/account_settings_fields',
        'js/student_account/views/account_settings_view',
    ], function (gettext, $, _, Backbone, UserAccountModel, UserPreferencesModel, FieldViews, AccountSettingsView) {

        return function (fieldsData, userAccountsApiUrl, userPreferencesApiUrl) {

            var accountSettingsElement = $('.wrapper-account-settings');

            var userAccountModel = new UserAccountModel();
            userAccountModel.url = userAccountsApiUrl;

            var userPreferencesModel = new UserPreferencesModel();
            userPreferencesModel.url = userPreferencesApiUrl;

            var sectionsData = [
                 {
                    title: gettext('Basic Account Information'),
                    fields: [
                        {
                            view: new FieldViews.ReadonlyFieldView({
                                model: userAccountModel,
                                title: gettext('Username'),
                                valueAttribute: 'username',
                                helpMessage: ''
                            })
                        },
                        {
                            view: new FieldViews.TextFieldView({
                                model: userAccountModel,
                                title: gettext('Full Name'),
                                valueAttribute: 'name',
                                helpMessage: gettext('This is the name used on your edX certificates. Changes to this field are reviewed.')
                            })
                        },
                        {
                            view: new FieldViews.EmailFieldView({
                                model: userAccountModel,
                                title: gettext('Email'),
                                valueAttribute: 'email',
                                helpMessage: gettext('The email address you use to sign in to edX. Communications from edX and your courses are sent to this address.')
                            })
                        },
                        {
                            view: new FieldViews.PasswordFieldView({
                                model: userAccountModel,
                                title: gettext('Password'),
                                valueAttribute: 'password',
                                emailAttribute: 'email',
                                linkTitle: gettext('Reset Password'),
                                linkHref: fieldsData['password']['url'],
                                helpMessage: gettext('When you click "Reset Password", a message will be sent to your email address. Click the link in the message to reset your password.')
                            })
                        },
                        {
                            view: new FieldViews.DropdownFieldView({
                                model: userPreferencesModel,
                                title: 'Language',
                                valueAttribute: 'pref-lang',
                                required: true,
                                refreshPageOnSave: true,
                                helpMessage: gettext('The language used for the edX site.'),
                                options: fieldsData['language']['options']
                            })
                        }
                    ]
                },
                {
                    title: gettext('Additional Information'),
                    fields: [
                        {
                            view: new FieldViews.DropdownFieldView({
                                model: userAccountModel,
                                title: gettext('Education Completed'),
                                valueAttribute: 'level_of_education',
                                options: fieldsData['level_of_education']['options']
                            })
                        },
                        {
                            view: new FieldViews.DropdownFieldView({
                                model: userAccountModel,
                                title: gettext('Gender'),
                                valueAttribute: 'gender',
                                options: fieldsData['gender']['options']
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
                            view: new FieldViews.DropdownFieldView({
                                model: userAccountModel,
                                title: gettext('Country or Region'),
                                valueAttribute: 'country',
                                options: fieldsData['country']['options']
                            })
                        },
                        {
                            view: new FieldViews.DropdownFieldView({
                                model: userAccountModel,
                                title: gettext('Preferred Language'),
                                valueAttribute: 'language',
                                helpMessage: gettext('If your preferred language isn\'t available as an edX language, you can indicate your preference here.'),
                                options: fieldsData['preferred_language']['options']
                            })
                        }
                    ]
                },
                {
                    title: gettext('Connected Accounts'),
                    fields: [
                        {
                            view: new FieldViews.LinkFieldView({
                                model: userAccountModel,
                                title: gettext('Facebook'),
                                valueAttribute: 'auth-facebook',
                                linkTitle: gettext('Link'),
                                helpMessage: gettext('Coming soon.')
                            })
                        },
                        {
                            view: new FieldViews.LinkFieldView({
                                model: userAccountModel,
                                title: gettext('Google'),
                                valueAttribute: 'auth-google',
                                linkTitle: gettext('Link'),
                                helpMessage: gettext('Coming soon.')
                            })
                        }
                    ]
                }
            ];

            var accountSettingsView = new AccountSettingsView({
                el: accountSettingsElement,
                sectionsData: sectionsData
            });

            accountSettingsView.render();

            var showLoadingError = function (model, response, options) {
                accountSettingsView.showLoadingError();
            };

            userAccountModel.fetch({
                success: function (model, response, options) {
                    userPreferencesModel.fetch({
                        success: function (model, response, options) {
                            accountSettingsView.renderFields();
                        },
                        error: showLoadingError
                    })
                },
                error: showLoadingError
            });

            return {
                userAccountModel: userAccountModel,
                userPreferencesModel: userPreferencesModel,
                accountSettingsView: accountSettingsView
            };
        };
    })
}).call(this, define || RequireJS.define);
