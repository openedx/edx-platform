define(['underscore', 'URI', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers'], function(_, URI, AjaxHelpers) {
    'use strict';

    var expectProfileElementContainsField = function(element, view) {
        var titleElement, fieldTitle;
        var $element = $(element);

        // Avoid testing for elements without titles
        titleElement = $element.find('.u-field-title');
        if (titleElement.length === 0) {
            return;
        }

        fieldTitle = titleElement.text().trim();
        if (!_.isUndefined(view.options.title) && !_.isUndefined(fieldTitle)) {
            expect(fieldTitle).toBe(view.options.title);
        }

        if ('fieldValue' in view || 'imageUrl' in view) {
            if ('imageUrl' in view) {
                expect($($element.find('.image-frame')[0]).attr('src')).toBe(view.imageUrl());
            } else if (view.fieldType === 'date') {
                expect(view.fieldValue()).toBe(view.timezoneFormattedDate());
            } else if (view.fieldValue()) {
                expect(view.fieldValue()).toBe(view.modelValue());
            } else if ('optionForValue' in view) {
                expect($($element.find('.u-field-value .u-field-value-readonly')[0]).text()).toBe(
                    view.displayValue(view.modelValue())
                );
            } else {
                expect($($element.find('.u-field-value .u-field-value-readonly')[0]).text()).toBe(view.modelValue());
            }
        } else {
            throw new Error('Unexpected field type: ' + view.fieldType);
        }
    };

    var expectProfilePrivacyFieldTobeRendered = function(learnerProfileView, othersProfile) {
        var $accountPrivacyElement = $('.wrapper-profile-field-account-privacy');
        var $privacyFieldElement = $($accountPrivacyElement).find('.u-field');

        if (othersProfile) {
            expect($privacyFieldElement.length).toBe(0);
        } else {
            expect($privacyFieldElement.length).toBe(1);
            expectProfileElementContainsField($privacyFieldElement, learnerProfileView.options.accountPrivacyFieldView);
        }
    };

    var expectSectionOneTobeRendered = function(learnerProfileView) {
        var sectionOneFieldElements = $(learnerProfileView.$('.wrapper-profile-section-one'))
            .find('.u-field, .social-links');

        expect(sectionOneFieldElements.length).toBe(7);
        expectProfileElementContainsField(sectionOneFieldElements[0], learnerProfileView.options.profileImageFieldView);
        expectProfileElementContainsField(sectionOneFieldElements[1], learnerProfileView.options.usernameFieldView);
        expectProfileElementContainsField(sectionOneFieldElements[2], learnerProfileView.options.nameFieldView);

        _.each(_.rest(sectionOneFieldElements, 3), function(sectionFieldElement, fieldIndex) {
            expectProfileElementContainsField(
                sectionFieldElement,
                learnerProfileView.options.sectionOneFieldViews[fieldIndex]
            );
        });
    };

    var expectSectionTwoTobeRendered = function(learnerProfileView) {
        var $sectionTwoElement = $('.wrapper-profile-section-two');
        var $sectionTwoFieldElements = $($sectionTwoElement).find('.u-field');

        expect($sectionTwoFieldElements.length).toBe(learnerProfileView.options.sectionTwoFieldViews.length);

        _.each($sectionTwoFieldElements, function(sectionFieldElement, fieldIndex) {
            expectProfileElementContainsField(
                sectionFieldElement,
                learnerProfileView.options.sectionTwoFieldViews[fieldIndex]
            );
        });
    };

    var expectProfileSectionsAndFieldsToBeRendered = function(learnerProfileView, othersProfile) {
        expectProfilePrivacyFieldTobeRendered(learnerProfileView, othersProfile);
        expectSectionOneTobeRendered(learnerProfileView);
        expectSectionTwoTobeRendered(learnerProfileView);
    };

    var expectLimitedProfileSectionsAndFieldsToBeRendered = function(learnerProfileView, othersProfile) {
        var sectionOneFieldElements = $('.wrapper-profile-section-one').find('.u-field');

        expectProfilePrivacyFieldTobeRendered(learnerProfileView, othersProfile);

        expect(sectionOneFieldElements.length).toBe(2);
        expectProfileElementContainsField(
            sectionOneFieldElements[0],
            learnerProfileView.options.profileImageFieldView
        );
        expectProfileElementContainsField(
            sectionOneFieldElements[1],
            learnerProfileView.options.usernameFieldView
        );

        if (othersProfile) {
            expect($('.profile-private-message').text())
                .toBe('This learner is currently sharing a limited profile.');
        } else {
            expect($('.profile-private-message').text()).toBe('You are currently sharing a limited profile.');
        }
    };

    var expectProfileSectionsNotToBeRendered = function() {
        expect($('.wrapper-profile-field-account-privacy').length).toBe(0);
        expect($('.wrapper-profile-section-one').length).toBe(0);
        expect($('.wrapper-profile-section-two').length).toBe(0);
    };

    var expectTabbedViewToBeUndefined = function(requests, tabbedViewView) {
        // Unrelated initial request, no badge request
        expect(requests.length).toBe(1);
        expect(tabbedViewView).toBe(undefined);
    };

    var expectTabbedViewToBeShown = function(tabbedViewView) {
        expect(tabbedViewView.$el.find('.page-content-nav').is(':visible')).toBe(true);
    };

    return {
        expectLimitedProfileSectionsAndFieldsToBeRendered: expectLimitedProfileSectionsAndFieldsToBeRendered,
        expectProfileSectionsAndFieldsToBeRendered: expectProfileSectionsAndFieldsToBeRendered,
        expectProfileSectionsNotToBeRendered: expectProfileSectionsNotToBeRendered,
        expectTabbedViewToBeUndefined: expectTabbedViewToBeUndefined,
        expectTabbedViewToBeShown: expectTabbedViewToBeShown
    };
});
