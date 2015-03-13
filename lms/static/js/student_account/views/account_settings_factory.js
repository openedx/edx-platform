;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone',
        'js/student_account/models/account_settings_models',
        'js/student_account/views/account_settings_fields',
        'js/student_account/views/account_settings_view',
    ], function (gettext, $, _, Backbone, AccountSettingsModel, AccountSettingsFieldViews, AccountSettingsView) {

        var setupAccountSettingsSection = function (fields_data) {

            var accountSettingsElement = $('.account-settings-container');
            var accountSettingsModel = new AccountSettingsModel();
            accountSettingsModel.url = accountSettingsElement.data('accounts-api-url');

            var accountSettingsView = new AccountSettingsView({
                el: accountSettingsElement,
                model: accountSettingsModel,
                context: {
                    accountSettingsModelUrl: accountSettingsModel.url
                },
                sections: [
                    {
                        title: gettext("Basic Account Information"),
                        fields: [
                            {
                                view: new AccountSettingsFieldViews.ReadonlyFieldView({
                                    model: accountSettingsModel,
                                    title: gettext("Username"),
                                    valueAttribute: "username",
                                    helpMessage: "",
                                })
                            },
                            {
                                view: new AccountSettingsFieldViews.TextFieldView({
                                    model: accountSettingsModel,
                                    title: gettext("Full Name"),
                                    valueAttribute: "name",
                                    helpMessage: gettext("This is used on your edX certificates, and all changes are reviewed."),
                                })
                            },
                            {
                                view: new AccountSettingsFieldViews.EmailFieldView({
                                    model: accountSettingsModel,
                                    title: gettext("Email"),
                                    valueAttribute: "email",
                                    helpMessage: gettext("You account email is used as a login mechanism and for course communications."),
                                })
                            },
                            {
                                view: new AccountSettingsFieldViews.PasswordFieldView({
                                    model: accountSettingsModel,
                                    title: gettext("Password"),
                                    valueAttribute: "password",
                                    emailAttribute: "email",
                                    linkTitle: gettext("Reset Password"),
                                    linkHref: fields_data['password']['url'],
                                    helpMessage: gettext("To reset your password you'll need to click the reset password link sent to you via email."),
                                })
                            },
                            {
                                view: new AccountSettingsFieldViews.DropdownFieldView({
                                    model: accountSettingsModel,
                                    title: "Language",
                                    valueAttribute: "pref-lang",
                                    required: true,
                                    refreshPageOnSave: true,
                                    helpMessage: gettext("This setting controls your default edX language."),
                                    options: fields_data['language']['options'],
                                })
                            },
                        ]
                    },
                    {
                        title: gettext("Demographics and Additional Details"),
                        fields: [
                            {
                                view: new AccountSettingsFieldViews.DropdownFieldView({
                                    model: accountSettingsModel,
                                    title: gettext("Educational Background"),
                                    valueAttribute: "level_of_education",
                                    options: fields_data['level_of_education']['options'],
                                })
                            },
                            {
                                view: new AccountSettingsFieldViews.DropdownFieldView({
                                    model: accountSettingsModel,
                                    title: gettext("Gender"),
                                    valueAttribute: "gender",
                                    options: fields_data['gender']['options'],
                                })
                            },
                            {
                                view: new AccountSettingsFieldViews.DropdownFieldView({
                                    model: accountSettingsModel,
                                    title: gettext("Year of Birth"),
                                    valueAttribute: "year_of_birth",
                                    options: fields_data['year_of_birth']['options'],
                                })
                            },
                            {
                                view: new AccountSettingsFieldViews.DropdownFieldView({
                                    model: accountSettingsModel,
                                    title: gettext("Country"),
                                    valueAttribute: "country",
                                    options: fields_data['country']['options'],
                                })
                            },
                            {
                                view: new AccountSettingsFieldViews.DropdownFieldView({
                                    model: accountSettingsModel,
                                    title: gettext("Preferred Language"),
                                    valueAttribute: "language",
                                    helpMessage: gettext("If your preferred language isn't available as an edX language, you can indicate your preferance here."),
                                    options: fields_data['preferred_language']['options'],
                                })
                            },
                        ]
                    },
                    {
                        title: gettext("Connected Accounts"),
                        fields: [
                            {
                                view: new AccountSettingsFieldViews.LinkFieldView({
                                    model: accountSettingsModel,
                                    title: gettext("Facebook"),
                                    valueAttribute: 'auth-facebook',
                                    linkTitle: gettext("Link"),
                                    helpMessage: gettext("Under construction."),
                                })
                            },
                            {
                                view: new AccountSettingsFieldViews.LinkFieldView({
                                    model: accountSettingsModel,
                                    title: gettext("Google"),
                                    valueAttribute: 'auth-google',
                                    linkTitle: gettext("Link"),
                                    helpMessage: gettext("Under construction."),
                                })
                            },
                        ]
                    }
                ]
            });

            accountSettingsView.render();
            accountSettingsModel.fetch().done(function (data, textStatus, jqXHR) {
                accountSettingsView.renderFields();
            });
        }

        return setupAccountSettingsSection;
    })
}).call(this, define || RequireJS.define);
