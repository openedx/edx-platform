define(['backbone', 'jquery', 'underscore', 'common/js/spec_helpers/ajax_helpers', 'common/js/spec_helpers/template_helpers',
        'js/views/fields',
        'js/spec/views/fields_helpers',
        'js/spec/student_account/account_settings_fields_helpers',
        'js/student_account/views/account_settings_fields',
        'js/student_account/models/user_account_model',
        'string_utils'],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, FieldViews, FieldViewsSpecHelpers,
              AccountSettingsFieldViewSpecHelpers, AccountSettingsFieldViews) {
        'use strict';

        describe("edx.AccountSettingsFieldViews", function () {

            var requests,
                timerCallback;

            beforeEach(function () {
                TemplateHelpers.installTemplate('templates/fields/field_readonly');
                TemplateHelpers.installTemplate('templates/fields/field_dropdown');
                TemplateHelpers.installTemplate('templates/fields/field_link');
                TemplateHelpers.installTemplate('templates/fields/field_text');

                timerCallback = jasmine.createSpy('timerCallback');
                jasmine.Clock.useMock();
            });

            it("sends request to reset password on clicking link in PasswordFieldView", function() {
                requests = AjaxHelpers.requests(this);

                var fieldData = FieldViewsSpecHelpers.createFieldData(AccountSettingsFieldViews.PasswordFieldView, {
                    linkHref: '/password_reset',
                    emailAttribute: 'email'
                });

                var view = new AccountSettingsFieldViews.PasswordFieldView(fieldData).render();
                view.$('.u-field-value > a').click();
                AjaxHelpers.expectRequest(requests, 'POST', '/password_reset', "email=legolas%40woodland.middlearth");
                AjaxHelpers.respondWithJson(requests, {"success": "true"});
                FieldViewsSpecHelpers.expectMessageContains(
                    view,
                    "We've sent a message to legolas@woodland.middlearth. " +
                    "Click the link in the message to reset your password."
                );
            });

            it("sends request to /i18n/setlang/ after changing language preference in LanguagePreferenceFieldView", function() {
                requests = AjaxHelpers.requests(this);

                var selector = '.u-field-value > select';
                var fieldData = FieldViewsSpecHelpers.createFieldData(AccountSettingsFieldViews.DropdownFieldView, {
                    valueAttribute: 'language',
                    options: FieldViewsSpecHelpers.SELECT_OPTIONS
                });

                var view = new AccountSettingsFieldViews.LanguagePreferenceFieldView(fieldData).render();

                var data = {'language': FieldViewsSpecHelpers.SELECT_OPTIONS[2][0]};
                view.$(selector).val(data[fieldData.valueAttribute]).change();
                FieldViewsSpecHelpers.expectAjaxRequestWithData(requests, data);
                AjaxHelpers.respondWithNoContent(requests);

                AjaxHelpers.expectRequest(
                    requests,
                    'POST',
                    '/i18n/setlang/',
                    'language=' + data[fieldData.valueAttribute]
                );
                AjaxHelpers.respondWithNoContent(requests);
                FieldViewsSpecHelpers.expectMessageContains(view, "Your changes have been saved.");

                data = {'language': FieldViewsSpecHelpers.SELECT_OPTIONS[1][0]};
                view.$(selector).val(data[fieldData.valueAttribute]).change();
                FieldViewsSpecHelpers.expectAjaxRequestWithData(requests, data);
                AjaxHelpers.respondWithNoContent(requests);

                AjaxHelpers.expectRequest(
                    requests,
                    'POST',
                    '/i18n/setlang/',
                    'language=' + data[fieldData.valueAttribute]
                );
                AjaxHelpers.respondWithError(requests, 500);
                FieldViewsSpecHelpers.expectMessageContains(
                    view,
                    "You must sign out and sign back in before your language changes take effect."
                );
            });

            it("reads and saves the value correctly for LanguageProficienciesFieldView", function() {
                requests = AjaxHelpers.requests(this);

                var selector = '.u-field-value > select';
                var fieldData = FieldViewsSpecHelpers.createFieldData(AccountSettingsFieldViews.DropdownFieldView, {
                    valueAttribute: 'language_proficiencies',
                    options: FieldViewsSpecHelpers.SELECT_OPTIONS
                });
                fieldData.model.set({'language_proficiencies': [{'code': FieldViewsSpecHelpers.SELECT_OPTIONS[0][0]}]});

                var view = new AccountSettingsFieldViews.LanguageProficienciesFieldView(fieldData).render();

                expect(view.modelValue()).toBe(FieldViewsSpecHelpers.SELECT_OPTIONS[0][0]);

                var data = {'language_proficiencies': [{'code': FieldViewsSpecHelpers.SELECT_OPTIONS[1][0]}]};
                view.$(selector).val(FieldViewsSpecHelpers.SELECT_OPTIONS[1][0]).change();
                FieldViewsSpecHelpers.expectAjaxRequestWithData(requests, data);
                AjaxHelpers.respondWithNoContent(requests);
            });

            it("correctly links and unlinks from AuthFieldView", function() {
                requests = AjaxHelpers.requests(this);

                var fieldData = FieldViewsSpecHelpers.createFieldData(FieldViews.LinkFieldView, {
                    title: 'Yet another social network',
                    helpMessage: '',
                    valueAttribute: 'auth-yet-another',
                    connected: true,
                    connectUrl: 'yetanother.com/auth/connect',
                    disconnectUrl: 'yetanother.com/auth/disconnect'
                });
                var view = new AccountSettingsFieldViews.AuthFieldView(fieldData).render();

                AccountSettingsFieldViewSpecHelpers.verifyAuthField(view, fieldData, requests);
            });
        });
    });
