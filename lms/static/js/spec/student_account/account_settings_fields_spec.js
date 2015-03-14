define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/student_account/models/account_settings_models', 'js/student_account/views/account_settings_view',
        'js/student_account/views/account_settings_fields', 'string_utils'],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, AccountSettingsModel, AccountSettingsView,
              AccountSettingsFieldViews) {
        'use strict';

        describe("AccountSettingsFieldViews", function () {

            var accountSettingsView, requests, createMockAccountSettingsModel,
                createMockAccountSettingsModelJson, createMockAccountSettingsSections,
                createFieldData, fieldValueChangeEventHandler;

            var fieldsViews = [
                AccountSettingsFieldViews.ReadonlyFieldView,
                AccountSettingsFieldViews.TextFieldView,
                AccountSettingsFieldViews.EmailFieldView,
                AccountSettingsFieldViews.DropdownFieldView,
                AccountSettingsFieldViews.LinkFieldView,
                AccountSettingsFieldViews.PasswordFieldView,
            ];

            var MOCK_USERNAME = 'Legolas',
                MOCK_FULLNAME = 'Legolas Thranduil',
                MOCK_EMAIL = 'legolas@woodland.middlearth',
                MOCK_LANGUAGE = [['si', 'sindarin'], ['el', 'elvish']],
                MOCK_COUNTRY = 'woodland',
                MOCK_DATE_JOINED = '',
                MOCK_GENDER = 'male',
                MOCK_GOALS = '',
                MOCK_LEVEL_OF_EDUCATION = null,
                MOCK_MAILING_ADDRESS = '',
                MOCK_YEAR_OF_BIRTH = null,

            fieldValueChangeEventHandler = function(test, data, respondWithErrorCode) {
                AjaxHelpers.expectJsonRequest(
                    requests, 'PATCH', '/mock_service/api/user/v0/accounts/user', data
                );

                if (_.isUndefined(respondWithErrorCode)) {
                    AjaxHelpers.respondWithNoContent(requests);
                } else {
                    AjaxHelpers.respondWithError(requests, respondWithErrorCode || 400);
                }
            };

            var createErrorMessage = function(attribute, user_message) {
                return {
                    responseText: '{"field_errors": { "' + attribute + '": { "user_message": "' + user_message + '" }}}',
                    status: 400,
                }
            }

            createFieldData = function (fieldType, fieldData) {
                var data = {
                    model: fieldData.model || createMockAccountSettingsModel({}),
                    title: fieldData.title || 'Field Title',
                    valueAttribute: fieldData.valueAttribute,
                    helpMessage: fieldData.helpMessage || 'I am a field message'
                };

                switch (fieldType) {
                    case AccountSettingsFieldViews.DropdownFieldView:
                        data['required'] = fieldData.required || false;
                        data['options'] = fieldData.options || [['1', 'Option1'], ['2', 'Option2'], ['3', 'Option3']];
                        break;
                    case AccountSettingsFieldViews.LinkFieldView:
                    case AccountSettingsFieldViews.PasswordFieldView:
                        data['linkTitle'] = fieldData.linkTitle || "Link Title";
                        data['linkHref'] = fieldData.linkHref || "/path/to/resource";
                        data['emailAttribute'] = 'email';
                        break;
                }

                return data;
            };

            createMockAccountSettingsModelJson = function (data) {
                return {
                    username: data.username || MOCK_USERNAME,
                    name: data.name || MOCK_FULLNAME,
                    email: data.email || MOCK_EMAIL,
                    password: data.password || '',
                    language: _.isUndefined(data.language) ? MOCK_LANGUAGE[0][0] : data.language,
                    country: data.country || MOCK_COUNTRY,
                    date_joined: data.date_joined || MOCK_DATE_JOINED,
                    gender: data.gender || MOCK_GENDER,
                    goals: data.goals || MOCK_GOALS,
                    level_of_education: data.level_of_education || MOCK_LEVEL_OF_EDUCATION,
                    mailing_address: data.mailing_address || MOCK_MAILING_ADDRESS,
                    year_of_birth: data.year_of_birth || MOCK_YEAR_OF_BIRTH
                };
            };

            createMockAccountSettingsModel = function (data) {
                var accountSettingsModel = new AccountSettingsModel(createMockAccountSettingsModelJson(data));
                accountSettingsModel.url = '/mock_service/api/user/v0/accounts/user';
                return accountSettingsModel;
            };

            var expectTitleAndMessageToBe = function(view, expectedTitle, expectedMessage) {
                expect(view.$('.account-settings-field-title').text().trim()).toBe(expectedTitle);
                expect(view.$('.account-settings-field-message').text().trim()).toBe(expectedMessage);
            };

            var expectMessageContains = function(view, expectedText) {
                expect(view.$('.account-settings-field-message').html()).toContain(expectedText);
            };

            var timerCallback;

            beforeEach(function () {
                TemplateHelpers.installTemplate('templates/student_account/account_settings');
                TemplateHelpers.installTemplate('templates/student_account/field_readonly');
                TemplateHelpers.installTemplate('templates/student_account/field_dropdown');
                TemplateHelpers.installTemplate('templates/student_account/field_link');
                TemplateHelpers.installTemplate('templates/student_account/field_text');

                timerCallback = jasmine.createSpy('timerCallback');
                jasmine.Clock.useMock();

            });

            it("updates messages correctly for all fields", function() {
                for (var i=0; i<fieldsViews.length; i++) {
                    var fieldView = fieldsViews[i];
                    var fieldData = createFieldData(fieldView, {
                        title: 'Username',
                        valueAttribute: 'username',
                        helpMessage: 'This is your login username.'
                    })

                    var view = new fieldView(fieldData).render()

                    var message = "This is field no." + i + "." ;
                    view.message(message);
                    expectMessageContains(view, message);

                    view.showHelpMessage();
                    expectMessageContains(view, view.helpMessage);

                    view.showInProgressMessage();
                    expectMessageContains(view, view.inProgressMessage);

                    view.showSuccessMessage();
                    expectMessageContains(view, view.successMessagePrefix);

                    expect(timerCallback).not.toHaveBeenCalled();

                    view.showErrorMessage(createErrorMessage(fieldData.valueAttribute, 'Please fix this.'));
                    expectMessageContains(view, view.invalidInputMessagePrefix);

                    view.showErrorMessage({status: 500});
                    expectMessageContains(view, view.errorMessage);
                }
            });

            it("resets success message after some time if it has not been already changed", function() {
                for (var i=0; i<fieldsViews.length; i++) {
                    var fieldView = fieldsViews[i];
                    var fieldData = createFieldData(fieldView, {
                        title: 'Username',
                        valueAttribute: 'username',
                        helpMessage: 'This is your login username.'
                    })

                    var view = new fieldView(fieldData).render()

                    view.showHelpMessage();
                    expectMessageContains(view, view.helpMessage);
                    view.showSuccessMessage();
                    expectMessageContains(view, view.successMessagePrefix);
                    jasmine.Clock.tick(5000);
                    // Message gets reset
                    expectMessageContains(view, view.helpMessage);

                    view.showSuccessMessage();
                    expectMessageContains(view, view.successMessagePrefix);
                    // But if we change the message, it should not get reset.
                    view.message("Do not reset this!");
                    jasmine.Clock.tick(5000);
                    expectMessageContains(view, "Do not reset this!");
                }
            });

            it("can correctly render readonly field", function() {
                var fieldData = createFieldData(AccountSettingsFieldViews.ReadonlyFieldView, {
                    title: 'Username',
                    valueAttribute: 'username',
                    helpMessage: 'This is your login username'
                });
                var view = new AccountSettingsFieldViews.ReadonlyFieldView(fieldData).render();

                expectTitleAndMessageToBe(view, fieldData.title, fieldData.helpMessage);
                expect(view.$('.account-settings-field-value').text().trim()).toBe(MOCK_USERNAME);
            });

            it("can correctly render text field", function() {
                var fieldData = createFieldData(AccountSettingsFieldViews.TextFieldView, {
                    title: 'Full Name',
                    valueAttribute: 'name',
                    helpMessage: 'This is used on your edX certificates, and all changes are reviewed.'
                });
                var view = new AccountSettingsFieldViews.TextFieldView(fieldData).render();

                expectTitleAndMessageToBe(view, fieldData.title, fieldData.helpMessage);
                expect(view.$('.account-settings-field-value > input').val()).toBe(MOCK_FULLNAME);
            });

            it("can correctly render dropdown field", function() {
                var fieldData = createFieldData(AccountSettingsFieldViews.DropdownFieldView, {
                    title: 'Language',
                    valueAttribute: 'language',
                    required: true,
                    options: MOCK_LANGUAGE,
                    helpMessage: 'This setting controls your default edX language.'
                });
                var view = new AccountSettingsFieldViews.DropdownFieldView(fieldData).render();

                // Required is set to true so selected value should match value in model.
                expectTitleAndMessageToBe(view, fieldData.title, fieldData.helpMessage);
                expect(view.$('.account-settings-field-value option:selected').val()).toBe(MOCK_LANGUAGE[0][0]);
                expect(view.$('.account-settings-field-value option:selected').text().trim()).toBe(MOCK_LANGUAGE[0][1]);

                // Required is set to false and model has no value for attribute, so selected value will be empty.
                fieldData.required = false;
                fieldData.model.set({'language': undefined});
                view = new AccountSettingsFieldViews.DropdownFieldView(fieldData).render();
                expectTitleAndMessageToBe(view, fieldData.title, fieldData.helpMessage);
                expect(view.$('.account-settings-field-value option:selected').val()).toBe('');
                expect(view.$('.account-settings-field-value option:selected').text().trim()).toBe('');
            });

            it("can correctly render link field", function() {
                var fieldData = createFieldData(AccountSettingsFieldViews.LinkFieldView, {
                    title: 'Title',
                    linkTitle: 'Link title',
                    helpMessage: 'Click the link.'
                });
                var view = new AccountSettingsFieldViews.LinkFieldView(fieldData).render();
                expectTitleAndMessageToBe(view, fieldData.title, fieldData.helpMessage);
                expect(view.$('.account-settings-field-value > a').text().trim()).toBe(fieldData.linkTitle);
            });

            it("can correctly render the text field help messages", function() {
                var textFieldSelector = '.account-settings-field-value > input';
                var messageSelector = '.account-settings-field-message';
                var data = {'name': 'Legolas Thranduil'};
                var fieldData = createFieldData(AccountSettingsFieldViews.TextFieldView, {
                    title: 'Full Name',
                    valueAttribute: 'name',
                    helpMessage: 'edX full name'
                });
                var textFieldView = new AccountSettingsFieldViews.TextFieldView(fieldData).render();
                requests = AjaxHelpers.requests(this);

                // Verify default message
                expect(textFieldView.$(messageSelector).text().trim()).toBe(fieldData.helpMessage);

                // Verify change in-progress message
                textFieldView.$(textFieldSelector).trigger('change');
                expect(textFieldView.$(messageSelector).text().trim()).toBe('Saving...');

                // Verify change completion message
                textFieldView.$(textFieldSelector).trigger('change');
                fieldValueChangeEventHandler(this, data);
                expect(textFieldView.$(messageSelector).text().trim()).toBe('Successfully changed.');

                // Verify server side issue/failure message
                textFieldView.$(textFieldSelector).val(data.name).change();
                fieldValueChangeEventHandler(this, data, 500);
                expect(textFieldView.$(messageSelector).text().trim()).toBe('An error occurred, please try again.');

                // Verify wrong input message
                // Empty the text field which is not a valid value, so we should get an error message
                textFieldView.errorMessage = '<i class="fa fa-exclamation-triangle"></i> Invalid Full Name value.';
                textFieldView.$(textFieldSelector).val('').change();
                fieldValueChangeEventHandler(this, {'name': ''}, 400);
                expect(textFieldView.$(messageSelector).text().trim()).toBe('Invalid Full Name value.');
            });

            it("can correctly render the dropdown field help messages", function() {
                var fieldValueSelector = '.account-settings-field-value > select';
                var messageSelector = '.account-settings-field-message';
                var data = {'language': 'si'};
                var fieldData = createFieldData(AccountSettingsFieldViews.DropdownFieldView, {
                    title: 'Language',
                    valueAttribute: 'language',
                    required: true,
                    options: MOCK_LANGUAGE,
                    helpMessage: 'edX Languge'
                });
                var dropdownFieldView = new AccountSettingsFieldViews.DropdownFieldView(fieldData).render();
                requests = AjaxHelpers.requests(this);

                // Verify default message
                expect(dropdownFieldView.$(messageSelector).text().trim()).toBe(fieldData.helpMessage);

                // Verify change in-progress message
                dropdownFieldView.$(fieldValueSelector).trigger('change');
                expect(dropdownFieldView.$(messageSelector).text().trim()).toBe('Saving...');

                // Verify change completion message
                dropdownFieldView.$(fieldValueSelector).trigger('change');
                fieldValueChangeEventHandler(this, data);
                expect(dropdownFieldView.$(messageSelector).text().trim()).toBe('Successfully changed.');

                // Verify server side issue/failure message
                dropdownFieldView.$(fieldValueSelector).trigger('change');
                fieldValueChangeEventHandler(this, data, 500);
                expect(dropdownFieldView.$(messageSelector).text().trim()).toBe('An error occurred, please try again.');

                // Verify wrong input message
                // Empty the text field which is not a valid value, so we should get an error message
                dropdownFieldView.errorMessage = '<i class="fa fa-exclamation-triangle"></i> Invalid language value.';
                dropdownFieldView.$(fieldValueSelector).change();
                fieldValueChangeEventHandler(this, data, 400);
                expect(dropdownFieldView.$(messageSelector).text().trim()).toBe('Invalid language value.');
            });

            it("shows correct behaviour for password reset", function() {
                var fieldData = createFieldData(AccountSettingsFieldViews.PasswordFieldView, {
                    linkHref: '/password_reset'
                });
                spyOn($, "ajax");
                var passwordFieldView = new AccountSettingsFieldViews.PasswordFieldView(fieldData).render();
                passwordFieldView.$('.account-settings-field-value > a').click();
                $.ajax.mostRecentCall.args[0].success();
                expect($.ajax.mostRecentCall.args[0]["url"]).toEqual(fieldData.linkHref);
                expect($.ajax.mostRecentCall.args[0]["type"].toUpperCase()).toEqual("POST");
                expect($.ajax.mostRecentCall.args[0]["data"]).toEqual({email: MOCK_EMAIL});
                expect(passwordFieldView.$('.account-settings-field-message').text().trim()).toBe(
                    "Complete you password reset using the confirmation link emailed to legolas@woodland.middlearth."
                );
            });
        });
    });
