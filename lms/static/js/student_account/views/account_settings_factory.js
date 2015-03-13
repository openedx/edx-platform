var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.setupAccountSettingsViews = function(fields_data) {
        var accountSettingsElement = $('.account-settings-container');
        var accountSettingsModel = new edx.student.account.AccountSettingsModel();
        accountSettingsModel.url = accountSettingsElement.data('accounts-api-url');

        var accountSettingsView = new edx.student.account.AccountSettingsView({
            el: accountSettingsElement,
            model: accountSettingsModel,
            context: {
                accountSettingsModelUrl: accountSettingsModel.url
            },
            sections: [
                {
                    title: "Basic Account Information",
                    fields: [
                        {
                            view: new edx.student.account.fieldViews.ReadonlyFieldView({
                                model: accountSettingsModel,
                                title: "Username",
                                valueAttribute: "username",
                                helpMessage: ""
                            })
                        },
                        {
                            view: new edx.student.account.fieldViews.TextFieldView({
                                model: accountSettingsModel,
                                title: "Full Name",
                                valueAttribute: "name",
                                helpMessage: "This is used on your edX certificates, and all changes are reviewed."
                            })
                        },
                        {
                            view: new edx.student.account.fieldViews.TextFieldView({
                                model: accountSettingsModel,
                                title: "Email",
                                valueAttribute: "email",
                                helpMessage: "You account email is used as a login mechanism and for course communications."
                            })
                        },
                        {
                            view: new edx.student.account.fieldViews.PasswordFieldView({
                                model: accountSettingsModel,
                                id: "password",
                                title: "Password",
                                dataAttribute: "email",
                                linkTitle: "Reset Password",
                                linkHref: fields_data['password']['url'],
                                helpMessage: "To reset your password you'll need to click the reset password link sent to you via email."
                            })
                        },
                        {
                            view: new edx.student.account.fieldViews.DropdownFieldView({
                                model: accountSettingsModel,
                                title: "Language",
                                valueAttribute: "language",
                                defaultValue: fields_data['language']['default'],
                                required: true,
                                helpMessage: "This setting controls your default edX language.",
                                options: fields_data['language']['options'],
                            })
                        },
                    ]
                },
                {
                    title: "Demographics and Additional Details",
                    fields: [
                        {
                            view: new edx.student.account.fieldViews.DropdownFieldView({
                                model: accountSettingsModel,
                                title: "Educational Background",
                                valueAttribute: "level_of_education",
                                defaultValue: null,
                                required: false,
                                options: fields_data['level_of_education']['options'],
                            })
                        },
                        {
                            view: new edx.student.account.fieldViews.DropdownFieldView({
                                model: accountSettingsModel,
                                title: "Gender",
                                valueAttribute: "gender",
                                defaultValue: null,
                                required: false,
                                options: fields_data['gender']['options'],
                            })
                        },
                        {
                            view: new edx.student.account.fieldViews.DropdownFieldView({
                                model: accountSettingsModel,
                                title: "Year of Birth",
                                valueAttribute: "year_of_birth",
                                defaultValue: null,
                                required: false,
                                options: fields_data['year_of_birth']['options'],
                            })
                        },
                        {
                            view: new edx.student.account.fieldViews.DropdownFieldView({
                                model: accountSettingsModel,
                                title: "Country",
                                valueAttribute: "null",
                                defaultValue: null,
                                required: false,
                                options: fields_data['country']['options'],
                            })
                        },
                        {
                            view: new edx.student.account.fieldViews.DropdownFieldView({
                                model: accountSettingsModel,
                                title: "Time Zone",
                                valueAttribute: "timezone",
                                defaultValue: null,
                                required: false,
                                options: fields_data['timezone']['options'],
                            })
                        },
                        {
                            view: new edx.student.account.fieldViews.DropdownFieldView({
                                model: accountSettingsModel,
                                title: "Preferred Language",
                                valueAttribute: "preferred_language",
                                defaultValue: null,
                                required: false,
                                helpMessage: "If your preferred language isn't available as an edX language, you can indicate your preferance here.",
                                options: fields_data['preferred_language']['options'],
                            })
                        },
                    ]
                },
                {
                    title: "Connected Accounts",
                    fields: [
                        {
                            view: new edx.student.account.fieldViews.LinkFieldView({
                                id: 'auth-facebook',
                                model: accountSettingsModel,
                                title: "Facebook",
                                linkTitle: "Link",
                            })
                        },
                        {
                            view: new edx.student.account.fieldViews.LinkFieldView({
                                id: 'auth-google',
                                model: accountSettingsModel,
                                title: "Google",
                                linkTitle: "Link",
                            })
                        },
                    ]
                }
            ]
        });

        accountSettingsView.render();
        accountSettingsModel.fetch().done(function (data, textStatus, jqXHR) {
            accountSettingsView.setupFields();
        });
    }


}).call(this, $, _, Backbone, gettext);
