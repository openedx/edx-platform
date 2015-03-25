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
        language: '2',
        bio: "About the student"
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

    var expectProfileElementContainsField = function(element, view) {
        var $element = $(element);
        var fieldTitle = $element.find('.u-field-title').text().trim();

        if (!_.isUndefined(view.options.title)) {
            if (view.modelValue()) {
                expect(fieldTitle).toBe(view.options.title);
            } else {
                expect(fieldTitle).toBe('+ ' + view.options.title);
            }
        }

        if ('fieldValue' in view) {
            expect(view.model.get(view.options.valueAttribute)).toBeTruthy();

            if (view.fieldValue()) {
                expect(view.fieldValue()).toBe(view.modelValue());

            } else if ('optionForValue' in view) {
                expect($($element.find('.u-field-value')[0]).text()).toBe(view.optionForValue(view.modelValue())[1]);

            }else {
                expect($($element.find('.u-field-value')[0]).text()).toBe(view.modelValue());
            }
        } else {
            throw new Error('Unexpected field type: ' + view.fieldType);
        }
    };

    var expectProfilePrivacyFieldTobeRendered = function(learnerProfileView, othersProfile) {

        var accountPrivacyElement = learnerProfileView.$('.wrapper-profile-field-account-privacy');
        var privacyFieldElement = $(accountPrivacyElement).find('.u-field');

        if (othersProfile) {
            expect(privacyFieldElement.length).toBe(0);
        } else {
            expect(privacyFieldElement.length).toBe(1);
            expectProfileElementContainsField(privacyFieldElement, learnerProfileView.options.accountPrivacyFieldView)
        }
    };

    var expectSectionOneTobeRendered = function(learnerProfileView) {

        var sectionOneFieldElements = $(learnerProfileView.$('.wrapper-profile-section-one')).find('.u-field');

        expect(sectionOneFieldElements.length).toBe(learnerProfileView.options.sectionOneFieldViews.length);

        _.each(sectionOneFieldElements, function (sectionFieldElement, fieldIndex) {
            expectProfileElementContainsField(sectionFieldElement, learnerProfileView.options.sectionOneFieldViews[fieldIndex]);
        });
    };

    var expectSectionTwoTobeRendered = function(learnerProfileView) {

        var sectionTwoElement = learnerProfileView.$('.wrapper-profile-section-two');
        var sectionTwoFieldElements = $(sectionTwoElement).find('.u-field');

        expect(sectionTwoFieldElements.length).toBe(learnerProfileView.options.sectionTwoFieldViews.length);

         _.each(sectionTwoFieldElements, function (sectionFieldElement, fieldIndex) {
            expectProfileElementContainsField(sectionFieldElement, learnerProfileView.options.sectionTwoFieldViews[fieldIndex]);
        });
    };

    var expectProfileSectionsAndFieldsToBeRendered = function (learnerProfileView, othersProfile) {
        expectProfilePrivacyFieldTobeRendered(learnerProfileView, othersProfile);
        expectSectionOneTobeRendered(learnerProfileView);
        expectSectionTwoTobeRendered(learnerProfileView);
    };

    var expectLimitedProfileSectionsAndFieldsToBeRendered = function (learnerProfileView, othersProfile) {
        expectProfilePrivacyFieldTobeRendered(learnerProfileView, othersProfile);

        var sectionOneFieldElements = $(learnerProfileView.$('.wrapper-profile-section-one')).find('.u-field');

        expect(sectionOneFieldElements.length).toBe(1);
        _.each(sectionOneFieldElements, function (sectionFieldElement, fieldIndex) {
            expectProfileElementContainsField(sectionFieldElement, learnerProfileView.options.sectionOneFieldViews[fieldIndex]);
        });

        expect($('.profile-private--message').text()).toBe('This edX learner is not currently sharing their profile details.')
    };

    var expectProfileSectionsNotToBeRendered = function(learnerProfileView) {
        expect(learnerProfileView.$('.wrapper-profile-field-account-privacy').length).toBe(0);
        expect(learnerProfileView.$('.wrapper-profile-section-one').length).toBe(0);
        expect(learnerProfileView.$('.wrapper-profile-section-two').length).toBe(0);
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
        expectSettingsSectionsAndFieldsToBeRendered: expectSettingsSectionsAndFieldsToBeRendered,
        // Profile page helper methods.
        expectLimitedProfileSectionsAndFieldsToBeRendered: expectLimitedProfileSectionsAndFieldsToBeRendered,
        expectProfileSectionsAndFieldsToBeRendered: expectProfileSectionsAndFieldsToBeRendered,
        expectProfileSectionsNotToBeRendered: expectProfileSectionsNotToBeRendered

    };
});
