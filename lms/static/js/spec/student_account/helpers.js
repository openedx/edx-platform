define(['underscore'], function(_) {
    'use strict';

    var USER_ACCOUNTS_API_URL = '/api/user/v0/accounts/student';
    var USER_PREFERENCES_API_URL = '/api/user/v0/preferences/student';
    var BADGES_API_URL = '/api/badges/v1/assertions/user/student/';
    var IMAGE_UPLOAD_API_URL = '/api/profile_images/v0/staff/upload';
    var IMAGE_REMOVE_API_URL = '/api/profile_images/v0/staff/remove';
    var FIND_COURSES_URL = '/courses';
    var PASSWORD_RESET_SUPPORT_LINK = 'https://support.edx.org/hc/en-us/articles/206212088-What-if-I-did-not-receive-a-password-reset-message-'; // eslint-disable-line max-len
    var PLATFORM_NAME = 'edX';
    var CONTACT_EMAIL = 'info@example.com';
    var PROFILE_IMAGE = {
        image_url_large: '/media/profile-images/image.jpg',
        has_image: true
    };
    var FIELD_OPTIONS = [
        ['0', 'Option 0'],
        ['1', 'Option 1'],
        ['2', 'Option 2'],
        ['3', 'Option 3']
    ];
    var TIME_ZONE_RESPONSE = [{
        time_zone: 'America/Guyana',
        description: 'America/Guyana (ECT, UTC-0500)'
    }];
    var FIELDS_DATA = {
        country: {
            options: FIELD_OPTIONS
        }, gender: {
            options: FIELD_OPTIONS
        }, language: {
            options: FIELD_OPTIONS
        }, level_of_education: {
            options: FIELD_OPTIONS
        }, password: {
            url: '/password_reset'
        }, year_of_birth: {
            options: FIELD_OPTIONS
        }, preferred_language: {
            options: FIELD_OPTIONS
        }, time_zone: {
            options: FIELD_OPTIONS
        }
    };
    var AUTH_DATA = {
        providers: [
            {
                id: 'oa2-network1',
                name: 'Network1',
                connected: true,
                accepts_logins: 'true',
                connect_url: 'yetanother1.com/auth/connect',
                disconnect_url: 'yetanother1.com/auth/disconnect'
            },
            {
                id: 'oa2-network2',
                name: 'Network2',
                connected: true,
                accepts_logins: 'true',
                connect_url: 'yetanother2.com/auth/connect',
                disconnect_url: 'yetanother2.com/auth/disconnect'
            }
        ]
    };
    var IMAGE_MAX_BYTES = 1024 * 1024;
    var IMAGE_MIN_BYTES = 100;
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
        bio: 'About the student',
        language_proficiencies: [{code: '1'}],
        profile_image: PROFILE_IMAGE,
        accomplishments_shared: false
    };
    var DEFAULT_USER_PREFERENCES_DATA = {
        'pref-lang': '2',
        'time_zone': null
    };

    var createAccountSettingsData = function(options) {
        return _.extend(_.extend({}, DEFAULT_ACCOUNT_SETTINGS_DATA), options);
    };

    var createUserPreferencesData = function(options) {
        return _.extend(_.extend({}, DEFAULT_USER_PREFERENCES_DATA), options);
    };

    var expectLoadingIndicatorIsVisible = function(view, visible) {
        if (visible) {
            expect($('.ui-loading-indicator')).not.toHaveClass('is-hidden');
        } else {
            expect($('.ui-loading-indicator')).toHaveClass('is-hidden');
        }
    };

    var expectLoadingErrorIsVisible = function(view, visible) {
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
        } else if (view.fieldType === 'button') {
            expect($(element).find('button').length).toBe(1);
        } else {
            throw new Error('Unexpected field type: ' + view.fieldType);
        }
    };

    var expectSettingsSectionsAndFieldsToBeRendered = function(accountSettingsView, fieldsAreRendered) {
        var sectionsData = accountSettingsView.options.tabSections.aboutTabSections;

        var sectionElements = accountSettingsView.$('#aboutTabSections-tabpanel .section');
        expect(sectionElements.length).toBe(sectionsData.length);

        _.each(sectionElements, function(sectionElement, sectionIndex) {
            expect($(sectionElement).find('.section-header').text()
                .trim()).toBe(sectionsData[sectionIndex].title);

            var sectionFieldElements = $(sectionElement).find('.u-field');

            if (fieldsAreRendered === false) {
                expect(sectionFieldElements.length).toBe(0);
            } else {
                expect(sectionFieldElements.length).toBe(sectionsData[sectionIndex].fields.length);

                _.each(sectionFieldElements, function(sectionFieldElement, fieldIndex) {
                    expectElementContainsField(sectionFieldElement, sectionsData[sectionIndex].fields[fieldIndex]);
                });
            }
        });
    };

    var expectSettingsSectionsButNotFieldsToBeRendered = function(accountSettingsView) {
        expectSettingsSectionsAndFieldsToBeRendered(accountSettingsView, false);
    };

    return {
        USER_ACCOUNTS_API_URL: USER_ACCOUNTS_API_URL,
        USER_PREFERENCES_API_URL: USER_PREFERENCES_API_URL,
        BADGES_API_URL: BADGES_API_URL,
        FIND_COURSES_URL: FIND_COURSES_URL,
        IMAGE_UPLOAD_API_URL: IMAGE_UPLOAD_API_URL,
        IMAGE_REMOVE_API_URL: IMAGE_REMOVE_API_URL,
        PASSWORD_RESET_SUPPORT_LINK: PASSWORD_RESET_SUPPORT_LINK,
        PLATFORM_NAME: PLATFORM_NAME,
        CONTACT_EMAIL: CONTACT_EMAIL,
        PROFILE_IMAGE: PROFILE_IMAGE,
        FIELD_OPTIONS: FIELD_OPTIONS,
        TIME_ZONE_RESPONSE: TIME_ZONE_RESPONSE,
        FIELDS_DATA: FIELDS_DATA,
        AUTH_DATA: AUTH_DATA,
        IMAGE_MAX_BYTES: IMAGE_MAX_BYTES,
        IMAGE_MIN_BYTES: IMAGE_MIN_BYTES,
        createAccountSettingsData: createAccountSettingsData,
        createUserPreferencesData: createUserPreferencesData,
        expectLoadingIndicatorIsVisible: expectLoadingIndicatorIsVisible,
        expectLoadingErrorIsVisible: expectLoadingErrorIsVisible,
        expectElementContainsField: expectElementContainsField,
        expectSettingsSectionsButNotFieldsToBeRendered: expectSettingsSectionsButNotFieldsToBeRendered,
        expectSettingsSectionsAndFieldsToBeRendered: expectSettingsSectionsAndFieldsToBeRendered
    };
});
