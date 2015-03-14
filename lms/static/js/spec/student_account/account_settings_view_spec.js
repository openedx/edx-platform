define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/student_account/models/account_settings_models', 'js/student_account/views/account_settings_view',
        'js/student_account/views/account_settings_fields'],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, AccountSettingsModel, AccountSettingsView,
              AccountSettingsFieldViews) {
        'use strict';

        describe("Account Settings View", function () {
            var createAccountSettingsView, accountSettingsView, requests, createMockAccountSettingsModel,
                createMockAccountSettingsModelJson, createMockAccountSettingsSections, verifyFieldValues,
                createMockAccountSettingsSectionsField, createMockAccountSettingsSectionsFieldJson, getFieldInfo,
                createMockSectionsFields, fieldValueChangeEventHandler;

            var MOCK_USERNAME, MOCK_FULLNAME, MOCK_EMAIL, MOCK_LANGUAGE, MOCK_COUNTRY, MOCK_DATE_JOINED, MOCK_GENDER,
                MOCK_GOALS, MOCK_LEVEL_OF_EDUCATION, MOCK_MAILING_ADDRESS, MOCK_YEAR_OF_BIRTH, SECTIONS_TITLES,
                TYPE_READONLY, TYPE_TEXT, TYPE_DROPDOWN, TYPE_LINK, TYPE_PASSWORD, FIELD_VIEWS;

            MOCK_USERNAME = 'Legolas';
            MOCK_FULLNAME = 'Legolas Thranduil';
            MOCK_EMAIL = 'legolas@woodland.middlearth';
            MOCK_LANGUAGE = [['si', 'sindarin'], ['el', 'elvish']];
            MOCK_COUNTRY = 'woodland';
            MOCK_DATE_JOINED = '';
            MOCK_GENDER = 'male';
            MOCK_GOALS = '';
            MOCK_LEVEL_OF_EDUCATION = null;
            MOCK_MAILING_ADDRESS = '';
            MOCK_YEAR_OF_BIRTH = null;

            SECTIONS_TITLES = [
                'Basic Account Information',
                'Demographics and Additional Details',
                'Connected Accounts'
            ];

            TYPE_READONLY = 0;
            TYPE_TEXT = 1;
            TYPE_DROPDOWN = 2;
            TYPE_LINK = 3;
            TYPE_PASSWORD = 4;

            FIELD_VIEWS = [
                AccountSettingsFieldViews.ReadonlyFieldView,
                AccountSettingsFieldViews.TextFieldView,
                AccountSettingsFieldViews.DropdownFieldView,
                AccountSettingsFieldViews.LinkFieldView,
                AccountSettingsFieldViews.PasswordFieldView
            ];

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

            getFieldInfo = function (fieldType, fieldElement) {
                var fieldValue, fieldInfo = {};

                switch (fieldType) {
                    case TYPE_READONLY:
                        fieldValue = $(fieldElement).find('.account-settings-field-value').text().trim();
                        break;
                    case TYPE_TEXT:
                        fieldValue = $(fieldElement).find('.account-settings-field-value > input').val();
                        break;
                    case TYPE_DROPDOWN:
                        fieldInfo['code'] = $(fieldElement).find('.account-settings-field-value option:selected').val();
                        fieldValue = $(fieldElement).find('.account-settings-field-value option:selected').text().trim();
                        break;
                    case TYPE_LINK:
                        fieldValue = $(fieldElement).find('.account-settings-field-value > a').attr('href');
                        fieldInfo['linkTitle'] = $(fieldElement).find('.account-settings-field-value > a').text().trim();
                        break;
                }

                fieldInfo['title'] = $(fieldElement).find('.account-settings-field-title').text().trim();
                fieldInfo['value'] = fieldValue;
                fieldInfo['helpMessage'] = $(fieldElement).find('.account-settings-field-message').text().trim();

                return fieldInfo;
            };

            createMockSectionsFields = function () {
               return [
                   {
                       view: createMockAccountSettingsSectionsField(
                           TYPE_READONLY,
                           {
                               title: 'Username',
                               valueAttribute: 'username',
                               helpMessage: 'readonly msg'
                           },
                           false
                       )
                   },
                   {
                       view: createMockAccountSettingsSectionsField(
                           TYPE_TEXT,
                           {
                               title: 'Full Name',
                               valueAttribute: 'name',
                               helpMessage: 'text msg'
                           },
                           false
                       )
                   },
                   {
                       view: createMockAccountSettingsSectionsField(
                           TYPE_DROPDOWN,
                           {
                               title: 'Language',
                               valueAttribute: 'language',
                               required: true,
                               options: MOCK_LANGUAGE,
                               helpMessage: 'lang msg'
                           },
                           false
                       )
                   }
                ];
            };

            verifyFieldValues = function(fieldType, fieldElement, expectedValues) {
                var fieldInfo = getFieldInfo(fieldType, fieldElement);
                _.each(fieldInfo, function(value, key) {
                    expect(expectedValues).toContain(value);
                });
            };

            createMockAccountSettingsSectionsFieldJson = function (fieldType, fieldData) {
                var data = {
                    model: fieldData.model || createMockAccountSettingsModel({}),
                    title: fieldData.title || 'Field Title',
                    valueAttribute: fieldData.valueAttribute,
                    helpMessage: fieldData.helpMessage || 'I am a field message'
                };

                switch (fieldType) {
                    case TYPE_DROPDOWN:
                        data['required'] = fieldData.required || false;
                        data['options'] = fieldData.options || [['1', 'Option1'], ['2', 'Option2'], ['3', 'Option3']];
                        break;
                    case TYPE_LINK:
                    case TYPE_PASSWORD:
                        data['linkTitle'] = fieldData.linkTitle || "Link Title";
                        data['linkHref'] = fieldData.linkHref || "/path/to/resource";
                        data['emailAttribute'] = 'email';
                        break;
                }

                return data;
            };

            createMockAccountSettingsSectionsField = function (fieldType, fieldData, renderView) {
                var fieldView = FIELD_VIEWS[fieldType];
                var view = new fieldView(createMockAccountSettingsSectionsFieldJson(fieldType, fieldData));

                if (_.isUndefined(renderView) || renderView == true) {
                    view.render();
                }
                return view;
            };

            createMockAccountSettingsSections = function (section1Fields, section2Fields, section3Fields) {
                return [
                    { title: SECTIONS_TITLES[0], fields: section1Fields || [] },
                    { title: SECTIONS_TITLES[1], fields: section2Fields || [] },
                    { title: SECTIONS_TITLES[2], fields: section3Fields || [] }
                ];
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

            createAccountSettingsView = function (test, data) {
                var accountSettingsModel;

                accountSettingsModel = createMockAccountSettingsModel(data);
                requests = AjaxHelpers.requests(test);
                accountSettingsView = new AccountSettingsView({
                    el: $('.account-settings-container'),
                    model: accountSettingsModel,
                    context: {
                        accountSettingsModelUrl: accountSettingsModel.url
                    },
                    sections : data.sections || createMockAccountSettingsSections()
                });
                accountSettingsView.render();
                if (data.renderFields) {
                    accountSettingsView.renderFields();
                }
            };

            beforeEach(function () {
                setFixtures('<div class="account-settings-container"> </div>');
                TemplateHelpers.installTemplate('templates/student_account/account_settings');
                TemplateHelpers.installTemplate('templates/student_account/field_readonly');
                TemplateHelpers.installTemplate('templates/student_account/field_dropdown');
                TemplateHelpers.installTemplate('templates/student_account/field_link');
                TemplateHelpers.installTemplate('templates/student_account/field_text');
            });

            it("can render all sections as expected", function() {
                var expectedData = [
                    {type: TYPE_READONLY, values: ['Username', MOCK_USERNAME, 'readonly msg']},
                    {type: TYPE_TEXT, values: ['Full Name', MOCK_FULLNAME, 'text msg']},
                    {type: TYPE_DROPDOWN, values: ['Language', MOCK_LANGUAGE[0][0], MOCK_LANGUAGE[0][1], 'lang msg']}
                ];

                var section1Fields = createMockSectionsFields(),
                    section2Fields = createMockSectionsFields(),
                    section3Fields = createMockSectionsFields();

                sections = createMockAccountSettingsSections(section1Fields, section2Fields, section3Fields);
                createAccountSettingsView(this, {sections: sections, renderFields: true});

                var sections = accountSettingsView.$('.account-settings-section .account-settings-section-header');
                expect(sections.length).toBe(3);
                _.each(sections, function(section, index) {
                    expect($(section).text().trim()).toBe(SECTIONS_TITLES[index]);
                });

                sections = accountSettingsView.$('.account-settings-section');
                _.each(sections, function(section, sectionIndex) {
                    var fields = $(section).find('.account-settings-field');
                    _.each(fields, function(field, fieldIndex) {
                        verifyFieldValues(expectedData[fieldIndex].type, field, expectedData[fieldIndex].values);
                    });
                });
            });
        });
    });