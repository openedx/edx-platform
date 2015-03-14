define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/spec/student_account/helpers',
        'js/student_account/views/account_settings_fields',
        'js/student_account/models/user_account_model',
        'js/student_account/views/account_settings_view'
       ],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, Helpers, FieldViews, UserAccountModel, AccountSettingsView) {
        'use strict';

        describe("edx.user.AccountSettingsView", function () {

            var createAccountSettingsView = function () {

                var model = new UserAccountModel();
                model.set(Helpers.USER_ACCOUNTS_DATA);

                var sectionsData = [
                    {
                        title: "Basic Account Information",
                        fields: [
                            {
                                view: new FieldViews.ReadonlyFieldView({
                                    model: model,
                                    title: "Username",
                                    valueAttribute: "username"
                                })
                            },
                            {
                                view: new FieldViews.TextFieldView({
                                    model: model,
                                    title: "Full Name",
                                    valueAttribute: "name"
                                })
                            }
                        ]
                    },
                    {
                        title: "Additional Information",
                        fields: [
                            {
                                view: new FieldViews.DropdownFieldView({
                                    model: model,
                                    title: "Education Completed",
                                    valueAttribute: "level_of_education",
                                    options: Helpers.FIELD_OPTIONS
                                })
                            }
                        ]
                    }
                ]

                var accountSettingsView = new AccountSettingsView({
                    el: $('.wrapper-account-settings'),
                    model: model,
                    sectionsData : sectionsData
                });

                return accountSettingsView;
            };

            beforeEach(function () {
                setFixtures('<div class="wrapper-account-settings"></div>');
                TemplateHelpers.installTemplate('templates/fields/field_readonly');
                TemplateHelpers.installTemplate('templates/fields/field_dropdown');
                TemplateHelpers.installTemplate('templates/fields/field_link');
                TemplateHelpers.installTemplate('templates/fields/field_text');
                TemplateHelpers.installTemplate('templates/student_account/account_settings');
            });

            it("shows loading error correctly", function() {

                var accountSettingsView = createAccountSettingsView();

                accountSettingsView.render();
                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, true);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(accountSettingsView);

                accountSettingsView.showLoadingError();
                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, false);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, true);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(accountSettingsView);
            });

            it("renders all fields as expected", function() {

                var accountSettingsView = createAccountSettingsView();

                accountSettingsView.render();
                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, true);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(accountSettingsView);

                accountSettingsView.renderFields();
                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, false);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsAndFieldsToBeRendered(accountSettingsView)
            });

        });
    });
