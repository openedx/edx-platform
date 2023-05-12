// eslint-disable-next-line no-undef
define(['backbone',
    'jquery',
    'underscore',
    'edx-ui-toolkit/js/utils/html-utils',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'common/js/spec_helpers/template_helpers',
    'js/views/fields',
    'string_utils'],
function(Backbone, $, _, HtmlUtils, AjaxHelpers, TemplateHelpers, FieldViews) {
    'use strict';

    // eslint-disable-next-line no-var
    var API_URL = '/api/end_point/v1';

    // eslint-disable-next-line no-var
    var USERNAME = 'Legolas',
        FULLNAME = 'Legolas Thranduil',
        EMAIL = 'legolas@woodland.middlearth',
        SELECT_OPTIONS = [['si', 'sindarin'], ['el', 'elvish'], ['na', 'nandor']];

    // eslint-disable-next-line no-var
    var UserAccountModel = Backbone.Model.extend({
        idAttribute: 'username',
        defaults: {
            username: USERNAME,
            name: FULLNAME,
            email: EMAIL,
            language: SELECT_OPTIONS[0][0]
        },
        url: API_URL
    });

    // eslint-disable-next-line no-var
    var createFieldData = function(fieldType, fieldData) {
        // eslint-disable-next-line no-var
        var data = {
            model: fieldData.model || new UserAccountModel({}),
            title: fieldData.title || 'Field Title',
            valueAttribute: fieldData.valueAttribute,
            helpMessage: fieldData.helpMessage || 'I am a field message',
            placeholderValue: fieldData.placeholderValue || 'I am a placeholder message'
        };

        // eslint-disable-next-line default-case
        switch (fieldType) {
        case FieldViews.DropdownFieldView:
            data.required = fieldData.required || false;
            data.options = fieldData.options || SELECT_OPTIONS;
            break;
        case FieldViews.LinkFieldView:
        case FieldViews.PasswordFieldView:
            data.linkTitle = fieldData.linkTitle || 'Link Title';
            data.linkHref = fieldData.linkHref || '/path/to/resource';
            data.emailAttribute = 'email';
            break;
        }

        _.extend(data, fieldData);

        return data;
    };

    /* eslint-disable-next-line camelcase, no-var */
    var createErrorMessage = function(attribute, user_message) {
        /* eslint-disable-next-line camelcase, no-var */
        var field_errors = {};
        // eslint-disable-next-line camelcase
        field_errors[attribute] = {
            // eslint-disable-next-line camelcase
            user_message: user_message
        };
        return {
            // eslint-disable-next-line camelcase
            field_errors: field_errors
        };
    };

    // eslint-disable-next-line no-var
    var expectTitleToContain = function(view, expectedTitle) {
        expect(view.$('.u-field-title').text().trim()).toContain(expectedTitle);
    };

    // eslint-disable-next-line no-var
    var expectDropdownSrTitleToContain = function(view, expectedTitle) {
        expect(view.$('.u-field-value .sr').text().trim()).toContain(expectedTitle);
    };

    // eslint-disable-next-line no-var
    var expectMessageContains = function(view, expectedText) {
        expect(view.$('.u-field-message').html()).toContain(expectedText);
    };

    // eslint-disable-next-line no-var
    var expectTitleAndMessageToContain = function(view, expectedTitle, expectedMessage) {
        expectTitleToContain(view, expectedTitle);
        expectMessageContains(view, expectedMessage);
    };

    // eslint-disable-next-line no-var
    var expectAjaxRequestWithData = function(requests, data) {
        AjaxHelpers.expectJsonRequest(
            requests, 'PATCH', API_URL, data
        );
    };

    // eslint-disable-next-line no-var
    var verifyMessageUpdates = function(view, data, timerCallback) {
        // eslint-disable-next-line no-var
        var message = 'Here to help!';

        view.showHelpMessage(message);
        expectMessageContains(view, message);

        view.showHelpMessage();
        expectMessageContains(view, view.helpMessage);

        view.showInProgressMessage();
        expectMessageContains(view, view.indicators.inProgress);
        expectMessageContains(view, view.messages.inProgress);

        view.showSuccessMessage();
        expectMessageContains(view, view.indicators.success);
        expectMessageContains(view, view.getMessage('success'));

        expect(timerCallback).not.toHaveBeenCalled();

        view.showErrorMessage({
            responseText: JSON.stringify(createErrorMessage(data.valueAttribute, 'Ops, try again!.')),
            status: 400
        });
        expectMessageContains(view, view.indicators.validationError);

        view.showErrorMessage({status: 500});
        expectMessageContains(view, view.indicators.error);
        expectMessageContains(view, view.indicators.error);
    };

    // eslint-disable-next-line no-var
    var verifySuccessMessageReset = function(view) {
        view.showHelpMessage();
        expectMessageContains(view, view.helpMessage);
        view.showSuccessMessage();
        expectMessageContains(view, view.indicators.success);
        // eslint-disable-next-line no-undef
        jasmine.clock().tick(7000);
        // Message gets reset
        expectMessageContains(view, view.helpMessage);

        view.showSuccessMessage();
        expectMessageContains(view, view.indicators.success);
        // But if we change the message, it should not get reset.
        view.showHelpMessage('Do not reset this!');
        // eslint-disable-next-line no-undef
        jasmine.clock().tick(7000);
        expectMessageContains(view, 'Do not reset this!');
    };

    // eslint-disable-next-line no-var
    var verifyPersistence = function(fieldClass, requests) {
        // eslint-disable-next-line no-var
        var fieldData = createFieldData(fieldClass, {
            title: 'Username',
            valueAttribute: 'username',
            helpMessage: 'The username that you use to sign in to edX.',
            validValue: 'My Name',
            persistChanges: false,
            messagePosition: 'header'
        });
        // eslint-disable-next-line no-var
        var view = new fieldClass(fieldData).render();
        // eslint-disable-next-line no-var
        var valueInputSelector;

        // eslint-disable-next-line default-case
        switch (fieldClass) {
        case FieldViews.TextFieldView:
            valueInputSelector = '.u-field-value > input';
            break;
        case FieldViews.DropdownFieldView:
            valueInputSelector = '.u-field-value > select';
            _.extend(fieldData, {validValue: SELECT_OPTIONS[0][0]});
            break;
        case FieldViews.TextareaFieldView:
            valueInputSelector = '.u-field-value > textarea';
            break;
        }

        view.$(valueInputSelector).val(fieldData.validValue).change();
        expect(view.fieldValue()).toBe(fieldData.validValue);
        expectMessageContains(view, view.helpMessage);
        AjaxHelpers.expectNoRequests(requests);
    };

    // eslint-disable-next-line no-var
    var verifyEditableField = function(view, data, requests) {
        /* eslint-disable-next-line camelcase, no-var */
        var request_data = {};
        // eslint-disable-next-line no-var
        var url = view.model.url;

        if (data.editable === 'toggle') {
            expect(view.el).toHaveClass('mode-placeholder');
            expectTitleToContain(view, data.title);
            expectMessageContains(view, view.indicators.canEdit);
            view.$el.click();
        } else {
            expectTitleAndMessageToContain(view, data.title, data.helpMessage);
        }
        expect(view.el).toHaveClass('mode-edit');

        if (view.fieldValue() !== null) {
            expect(view.fieldValue()).not.toContain(data.validValue);
        }

        view.$(data.valueInputSelector).val(data.validValue).change();
        view.$(data.valueInputSelector).focusout();
        // When the value in the field is changed
        expect(view.fieldValue()).toBe(data.validValue);
        expectMessageContains(view, view.indicators.inProgress);
        expectMessageContains(view, view.messages.inProgress);
        // eslint-disable-next-line camelcase
        request_data[data.valueAttribute] = data.validValue;
        AjaxHelpers.expectJsonRequest(
            requests, 'PATCH', url, request_data
        );

        AjaxHelpers.respondWithNoContent(requests);
        // When server returns success.
        if (data.editable === 'toggle') {
            expect(view.el).toHaveClass('mode-display');
            view.$el.click();
        } else {
            expectMessageContains(view, view.indicators.success);
        }

        view.$(data.valueInputSelector).val(data.invalidValue1).change();
        view.$(data.valueInputSelector).focusout();
        // eslint-disable-next-line camelcase
        request_data[data.valueAttribute] = data.invalidValue1;
        AjaxHelpers.expectJsonRequest(
            requests, 'PATCH', url, request_data
        );
        AjaxHelpers.respondWithError(requests, 500);
        // When server returns a 500 error
        expectMessageContains(view, view.indicators.error);
        expectMessageContains(view, view.messages.error);
        expect(view.el).toHaveClass('mode-edit');

        view.$(data.valueInputSelector).val(data.invalidValue2).change();
        view.$(data.valueInputSelector).focusout();
        // eslint-disable-next-line camelcase
        request_data[data.valueAttribute] = data.invalidValue2;
        AjaxHelpers.expectJsonRequest(
            requests, 'PATCH', url, request_data
        );
        AjaxHelpers.respondWithError(requests, 400, createErrorMessage(data.valueAttribute, data.validationError));
        // When server returns a validation error
        expectMessageContains(view, view.indicators.validationError);
        expectMessageContains(view, data.validationError);
        expect(view.el).toHaveClass('mode-edit');

        view.$(data.valueInputSelector).val('').change();
        view.$(data.valueInputSelector).focusout();
        // When the value in the field is changed
        expect(view.fieldValue()).toBe(data.defaultValue);
        // eslint-disable-next-line camelcase
        request_data[data.valueAttribute] = data.defaultValue;
        AjaxHelpers.expectJsonRequest(
            requests, 'PATCH', url, request_data
        );
        AjaxHelpers.respondWithNoContent(requests);
        // When server returns success.
        if (data.editable === 'toggle') {
            expect(view.el).toHaveClass('mode-placeholder');
        } else {
            expect(view.el).toHaveClass('mode-edit');
        }
    };

    // eslint-disable-next-line no-var
    var verifyReadonlyField = function(view, data) {
        if (data.editable === 'toggle') {
            expect(view.el).toHaveClass('mode-placeholder');
            expectTitleToContain(view, data.title);
            expectMessageContains(view, view.indicators.canEdit);
            view.$el.click();
        } else {
            expectTitleAndMessageToContain(view, data.title, data.helpMessage);
        }
        expect(view.el).toHaveClass('u-field-readonly');

        if (view.fieldValue() !== null) {
            expect(view.fieldValue()).not.toContain(data.validValue);
        }
    };

    // eslint-disable-next-line no-var
    var verifyUneditableDropdownField = function(view, data) {
        expectTitleAndMessageToContain(view, data.title, data.helpMessage);
        expect(view.el).toHaveClass('u-field-dropdown');
        expect(view.el).toHaveClass('editable-never');
    };

    // eslint-disable-next-line no-var
    var verifyTextField = function(view, data, requests) {
        verifyEditableField(view, _.extend({
            valueSelector: '.u-field-value',
            valueInputSelector: '.u-field-value > input'
        }, data),
        requests);
    };

    // eslint-disable-next-line no-var
    var verifyReadonlyTextField = function(view, data) {
        verifyReadonlyField(view, _.extend({
            valueSelector: '.u-field-value'
        }, data));
    };

    // eslint-disable-next-line no-var
    var verifyDropDownField = function(view, data, requests) {
        verifyEditableField(view, _.extend({
            valueSelector: '.u-field-value',
            valueInputSelector: '.u-field-value > select'
        }, data
        ), requests);
    };

    // eslint-disable-next-line no-var
    var verifyReadonlyDropDownField = function(view, data) {
        verifyUneditableDropdownField(view, _.extend({
            valueSelector: '.editable-never'
        }, data));
    };

    return {
        SELECT_OPTIONS: SELECT_OPTIONS,
        UserAccountModel: UserAccountModel,
        createFieldData: createFieldData,
        createErrorMessage: createErrorMessage,
        expectTitleToContain: expectTitleToContain,
        expectDropdownSrTitleToContain: expectDropdownSrTitleToContain,
        expectTitleAndMessageToContain: expectTitleAndMessageToContain,
        expectMessageContains: expectMessageContains,
        expectAjaxRequestWithData: expectAjaxRequestWithData,
        verifyMessageUpdates: verifyMessageUpdates,
        verifySuccessMessageReset: verifySuccessMessageReset,
        verifyEditableField: verifyEditableField,
        verifyTextField: verifyTextField,
        verifyReadonlyTextField: verifyReadonlyTextField,
        verifyDropDownField: verifyDropDownField,
        verifyReadonlyDropDownField: verifyReadonlyDropDownField,
        verifyPersistence: verifyPersistence
    };
});
