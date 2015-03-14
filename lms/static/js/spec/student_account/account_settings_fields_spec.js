define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/views/fields',
        'js/student_account/views/account_settings_fields',
        'js/student_account/models/user_account_model',
        'string_utils'],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, FieldViews, AccountSettingsFieldViews, UserAccountModel) {
        'use strict';

        describe("edx.AccountSettingsFieldViews", function () {

            var requests,
                timerCallback;

            var USERNAME = 'Legolas',
                FULLNAME = 'Legolas Thranduil',
                EMAIL = 'legolas@woodland.middlearth',
                LANGUAGE = [['si', 'sindarin'], ['el', 'elvish']],
                COUNTRY = 'woodland',
                DATE_JOINED = '',
                GENDER = 'female',
                GOALS = '',
                LEVEL_OF_EDUCATION = null,
                MAILING_ADDRESS = '',
                YEAR_OF_BIRTH = null;

            var USER_ACCOUNT_API_URL = '/api/user/v0/accounts/user';

            var createMockUserAccountModel = function (data) {
                data = {
                    username: data.username || USERNAME,
                    name: data.name || FULLNAME,
                    email: data.email || EMAIL,
                    password: data.password || '',
                    language: _.isUndefined(data.language) ? LANGUAGE[0][0] : data.language,
                    country: data.country || COUNTRY,
                    date_joined: data.date_joined || DATE_JOINED,
                    gender: data.gender || GENDER,
                    goals: data.goals || GOALS,
                    level_of_education: data.level_of_education || LEVEL_OF_EDUCATION,
                    mailing_address: data.mailing_address || MAILING_ADDRESS,
                    year_of_birth: data.year_of_birth || YEAR_OF_BIRTH,
                    'pref-lang': LANGUAGE[0][0]
                };
                var model = new UserAccountModel(data);
                model.url = USER_ACCOUNT_API_URL;
                return model;
            };

            var createFieldData = function (fieldType, fieldData) {
                var data = {
                    model: createMockUserAccountModel({}),
                    title: 'Field Title',
                    helpMessage: 'I am a field message'
                };

                switch (fieldType) {
                    case FieldViews.DropdownFieldView:
                        data['required'] = false;
                        data['options'] = [['1', 'Option1'], ['2', 'Option2'], ['3', 'Option3']];
                        break;
                    case FieldViews.LinkFieldView:
                    case FieldViews.PasswordFieldView:
                        data['linkTitle'] = "Link Title";
                        data['linkHref'] = "/path/to/resource";
                        data['emailAttribute'] = 'email';
                        break;
                }

                _.extend(data, fieldData);

                return data;
            };

            var createErrorMessage = function(attribute, user_message) {
                var field_errors = {}
                field_errors[attribute] = {
                    "user_message": user_message
                }
                return {
                    "field_errors": field_errors
                }
            };

            var expectTitleAndMessageToBe = function(view, expectedTitle, expectedMessage) {
                expect(view.$('.u-field-title').text().trim()).toBe(expectedTitle);
                expect(view.$('.u-field-message').text().trim()).toBe(expectedMessage);
            };

            var expectMessageContains = function(view, expectedText) {
                expect(view.$('.u-field-message').html()).toContain(expectedText);
            };

            var expectAjaxRequestWithData = function(data) {
                AjaxHelpers.expectJsonRequest(
                    requests, 'PATCH', USER_ACCOUNT_API_URL, data
                );
            };

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

                var fieldData = createFieldData(AccountSettingsFieldViews.PasswordFieldView, {
                    linkHref: '/password_reset',
                    emailAttribute: 'email'
                });

                var view = new AccountSettingsFieldViews.PasswordFieldView(fieldData).render();
                view.$('.u-field-value > a').click();
                AjaxHelpers.expectRequest(requests, 'POST', '/password_reset', "email=legolas%40woodland.middlearth");
                AjaxHelpers.respondWithJson(requests, {"success": "true"})
                expectMessageContains(view,
                    "We've sent a message to legolas@woodland.middlearth. Click the link in the message to reset your password."
                );
            });

            it("sends request to /i18n/setlang/ after changing language preference in LanguagePreferenceFieldView", function() {
                requests = AjaxHelpers.requests(this);

                var fieldData = createFieldData(AccountSettingsFieldViews.PasswordFieldView, {
                    valueAttribute: 'pref-lang',
                    options: LANGUAGE
                });

                var view = new AccountSettingsFieldViews.LanguagePreferenceFieldView(fieldData).render();

                var data = {'pref-lang': LANGUAGE[1][0]};
                view.$('.u-field-value > select').val(data['pref-lang']).change();
                expectAjaxRequestWithData(data);
                AjaxHelpers.respondWithNoContent(requests);

                AjaxHelpers.expectRequest(requests, 'POST', '/i18n/setlang/', "language=el");
                AjaxHelpers.respondWithNoContent(requests);
                expectMessageContains(view, "Your changes have been saved");

                var data = {'pref-lang': LANGUAGE[1][0]};
                view.$('.u-field-value > select').val(data['pref-lang']).change();
                expectAjaxRequestWithData(data);
                AjaxHelpers.respondWithNoContent(requests);

                AjaxHelpers.expectRequest(requests, 'POST', '/i18n/setlang/', "language=el");
                AjaxHelpers.respondWithError(requests, 500);
                expectMessageContains(view, "Please log out and log in again to see the language change.");
            });

        });
    });
