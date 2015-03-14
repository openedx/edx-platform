define(['underscore'], function(_) {
    'use strict';

    var USER_ACCOUNTS_API_URL = '/api/user/v0/accounts/student';
    var USER_PREFERENCES_API_URL = '/api/user/v0/preferences/student';

    var USER_ACCOUNTS_DATA = {
        username: 'student',
        name: 'Student',
        email: 'student@edx.org',

        level_of_education: '1',
        gender: '2',
        year_of_birth: '3',
        country: '1',
        language: '2'
    };

    var USER_PREFERENCES_DATA = {
        'pref-lang': '2'
    };

    var FIELD_OPTIONS = [
        ['1', 'Option 1'],
        ['2', 'Option 2'],
        ['3', 'Option 3'],
    ];

    var expectLoadingIndicatorIsVisible = function (view, visible) {
        if (visible) {
            expect(view.$('.ui-loading-indicator')).not.toHaveClass('is-hidden');
        } else {
            expect(view.$('.ui-loading-indicator')).toHaveClass('is-hidden');
        }
    };

    var expectLoadingErrorIsVisible = function (view, visible) {
        if (visible) {
            expect(view.$('.ui-loading-error')).not.toHaveClass('is-hidden');
        } else {
            expect(view.$('.ui-loading-error')).toHaveClass('is-hidden');
        }
    };

    var expectElementContainsField = function(element, field) {
        var view = field.view;

        var fieldTitle = $(element).find('.u-field-title').text().trim();
        expect(fieldTitle).toBe(view.options.title);

        if ('fieldValue' in view) {
            expect(view.model.get(view.options.valueAttribute)).toBeTruthy();
            expect(view.fieldValue()).toBe(view.modelValue());
        } else if (view.fieldType === 'link') {
            expect($(element).find('a').length).toBe(1);
        } else {
            throw new Error('Unexpected field type: ' + view.fieldType);
        }
    };

    var expectSettingsSectionsButNotFieldsToBeRendered = function (accountSettingsView) {
        expectSettingsSectionsAndFieldsToBeRendered(accountSettingsView, false)
    };

    var expectSettingsSectionsAndFieldsToBeRendered = function (accountSettingsView, fieldsAreRendered) {
        var sectionsData = accountSettingsView.options.sectionsData;

        var sectionElements = accountSettingsView.$('.section');
        expect(sectionElements.length).toBe(sectionsData.length);

        _.each(sectionElements, function(sectionElement, sectionIndex) {
            expect($(sectionElement).find('.section-header').text().trim()).toBe(sectionsData[sectionIndex].title);

            var sectionFieldElements = $(sectionElement).find('.u-field');

            if (fieldsAreRendered === false) {
                expect(sectionFieldElements.length).toBe(0);
            } else {
                expect(sectionFieldElements.length).toBe(sectionsData[sectionIndex].fields.length);

                _.each(sectionFieldElements, function (sectionFieldElement, fieldIndex) {
                    expectElementContainsField(sectionFieldElement, sectionsData[sectionIndex].fields[fieldIndex]);
                });
            }
        });
    };

    return {
        USER_ACCOUNTS_API_URL: USER_ACCOUNTS_API_URL,
        USER_PREFERENCES_API_URL: USER_PREFERENCES_API_URL,
        USER_ACCOUNTS_DATA: USER_ACCOUNTS_DATA,
        USER_PREFERENCES_DATA: USER_PREFERENCES_DATA,
        FIELD_OPTIONS: FIELD_OPTIONS,
        expectLoadingIndicatorIsVisible: expectLoadingIndicatorIsVisible,
        expectLoadingErrorIsVisible: expectLoadingErrorIsVisible,
        expectElementContainsField: expectElementContainsField,
        expectSettingsSectionsButNotFieldsToBeRendered: expectSettingsSectionsButNotFieldsToBeRendered,
        expectSettingsSectionsAndFieldsToBeRendered: expectSettingsSectionsAndFieldsToBeRendered
    };
});
