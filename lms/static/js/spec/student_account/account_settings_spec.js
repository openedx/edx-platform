define(['backbone', 'jquery', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
    'js/student_account/models/AccountSettingsModel', 'js/student_account/views/AccountSettingsView'],
    function (Backbone, $, AjaxHelpers, TemplateHelpers, AccountSettingsModel, settingsViews) {
        'use strict';

        describe("Account Settings View", function () {
            var createAccountSettingsView, createMockAccountSettings, createMockAccountSettingsJson,
                accountSettingsView, requests;

            createMockAccountSettingsJson = function () {

            };

            createMockAccountSettings = function () {

            };

            createAccountSettingsView = function (test, options) {
                var accountSettings;

                accountSettings.url = '/mock_service/account/settings';
                requests = AjaxHelpers.requests(test);
                accountSettingsView = new settingsViews.AccountSettingsView({

                });
                settingsViews.AccountSettingsView.render();
            };

            beforeEach(function () {
                setFixtures('<div class="account-settings-container"> </div>');
                TemplateHelpers.installTemplate('templates/student_account/account_settings');
                TemplateHelpers.installTemplate('templates/student_account/field_readonly');
                TemplateHelpers.installTemplate('templates/student_account/field_dropdown');
                TemplateHelpers.installTemplate('templates/student_account/field_link');
                TemplateHelpers.installTemplate('templates/student_account/field_text');
            });

            it("can render sections as expected", function() {
                createAccountSettingsView();
            });
        });
    });
