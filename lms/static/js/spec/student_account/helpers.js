define(['underscore'], function(_) {
    'use strict';

    var USER_ACCOUNTS_API_URL = '/api/user/v0/accounts/student';
    var USER_PREFERENCES_API_URL = '/api/user/v0/preferences/student';
    var BADGES_API_URL = '/api/badges/v1/assertions/user/student/';
    var IMAGE_UPLOAD_API_URL = '/api/profile_images/v0/staff/upload';
    var IMAGE_REMOVE_API_URL = '/api/profile_images/v0/staff/remove';
    var FIND_COURSES_URL = '/courses';

    var PROFILE_IMAGE = {
        image_url_large: '/media/profile-images/image.jpg',
        has_image: true
    };

    var DEFAULT_ACCOUNT_SETTINGS_DATA = {
        username: 'student',
        name: 'Student',
        email: 'student@edx.org',
        level_of_education: null,
        gender: null,
        year_of_birth: '3',    // Note: test birth year range is a string from 0-3
        requires_parental_consent: false,
        country: '1',
        language: null,
        bio: "About the student",
        language_proficiencies: [{code: '1'}],
        profile_image: PROFILE_IMAGE,
        accomplishments_shared: false
    };

    var createAccountSettingsData = function(options) {
        return _.extend(_.extend({}, DEFAULT_ACCOUNT_SETTINGS_DATA), options);
    };

    var DEFAULT_USER_PREFERENCES_DATA = {
        'pref-lang': '2'
    };

    var createUserPreferencesData = function(options) {
        return _.extend(_.extend({}, DEFAULT_USER_PREFERENCES_DATA), options);
    };

    var FIELD_OPTIONS = [
        ['0', 'Option 0'],
        ['1', 'Option 1'],
        ['2', 'Option 2'],
        ['3', 'Option 3']
    ];

    var IMAGE_MAX_BYTES = 1024 * 1024;
    var IMAGE_MIN_BYTES = 100;

    var expectLoadingIndicatorIsVisible = function (view, visible) {
        if (visible) {
            expect($('.ui-loading-indicator')).not.toHaveClass('is-hidden');
        } else {
            expect($('.ui-loading-indicator')).toHaveClass('is-hidden');
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
        var sectionsData = accountSettingsView.options.tabSections.aboutTabSections;

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
        BADGES_API_URL: BADGES_API_URL,
        FIND_COURSES_URL: FIND_COURSES_URL,
        IMAGE_UPLOAD_API_URL: IMAGE_UPLOAD_API_URL,
        IMAGE_REMOVE_API_URL: IMAGE_REMOVE_API_URL,
        IMAGE_MAX_BYTES: IMAGE_MAX_BYTES,
        IMAGE_MIN_BYTES: IMAGE_MIN_BYTES,
        PROFILE_IMAGE: PROFILE_IMAGE,
        createAccountSettingsData: createAccountSettingsData,
        createUserPreferencesData: createUserPreferencesData,
        FIELD_OPTIONS: FIELD_OPTIONS,
        expectLoadingIndicatorIsVisible: expectLoadingIndicatorIsVisible,
        expectLoadingErrorIsVisible: expectLoadingErrorIsVisible,
        expectElementContainsField: expectElementContainsField,
        expectSettingsSectionsButNotFieldsToBeRendered: expectSettingsSectionsButNotFieldsToBeRendered,
        expectSettingsSectionsAndFieldsToBeRendered: expectSettingsSectionsAndFieldsToBeRendered,
    };
});
