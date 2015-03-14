define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/views/fields',
        'string_utils'],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, FieldViews) {
        'use strict';

        var API_URL = '/api/end_point/v1';

        var USERNAME = 'Legolas',
            FULLNAME = 'Legolas Thranduil',
            EMAIL = 'legolas@woodland.middlearth',
            SELECT_OPTIONS = [['si', 'sindarin'], ['el', 'elvish'], ['na', 'nandor']];

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

        var createFieldData = function (fieldType, fieldData) {
            var data = {
                model: fieldData.model || new UserAccountModel({}),
                title: fieldData.title || 'Field Title',
                valueAttribute: fieldData.valueAttribute,
                helpMessage: fieldData.helpMessage || 'I am a field message'
            };

            switch (fieldType) {
                case FieldViews.DropdownFieldView:
                    data['required'] = fieldData.required || false;
                    data['options'] = fieldData.options || SELECT_OPTIONS;
                    break;
                case FieldViews.LinkFieldView:
                case FieldViews.PasswordFieldView:
                    data['linkTitle'] = fieldData.linkTitle || "Link Title";
                    data['linkHref'] = fieldData.linkHref || "/path/to/resource";
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

        var expectAjaxRequestWithData = function(requests, data) {
            AjaxHelpers.expectJsonRequest(
                requests, 'PATCH', API_URL, data
            );
        };

        var verifyMessageUpdates = function (view, data, timerCallback) {

            var message = 'Here to help!'

            view.message(message);
            expectMessageContains(view, message);

            view.showHelpMessage();
            expectMessageContains(view, view.helpMessage);

            view.showInProgressMessage();
            expectMessageContains(view, view.indicators['inProgress']);
            expectMessageContains(view, view.messages['inProgress']);

            view.showSuccessMessage();
            expectMessageContains(view, view.indicators['success']);
            expectMessageContains(view, view.getMessage('success'));

            expect(timerCallback).not.toHaveBeenCalled();

            view.showErrorMessage({
                responseText: JSON.stringify(createErrorMessage(data.valueAttribute, 'Ops, try again!.')),
                status: 400
            });
            expectMessageContains(view, view.indicators['validationError']);

            view.showErrorMessage({status: 500});
            expectMessageContains(view, view.indicators['error']);
            expectMessageContains(view, view.indicators['error']);
        };

        var verifySuccessMessageReset = function (view, data, timerCallback) {
            view.showHelpMessage();
            expectMessageContains(view, view.helpMessage);
            view.showSuccessMessage();
            expectMessageContains(view, view.indicators['success']);
            jasmine.Clock.tick(5000);
            // Message gets reset
            expectMessageContains(view, view.helpMessage);

            view.showSuccessMessage();
            expectMessageContains(view, view.indicators['success']);
            // But if we change the message, it should not get reset.
            view.message("Do not reset this!");
            jasmine.Clock.tick(5000);
            expectMessageContains(view, "Do not reset this!");
        };

        var verifyEditableField = function (view, data, requests) {
            var request_data = {};
            var url = view.model.url;

            expectTitleAndMessageToBe(view, data.title, data.helpMessage);

            view.$(data.valueElementSelector).val(data.validValue).change();
            // When the value in the field is changed
            expect(view.fieldValue()).toBe(data.validValue);
            expectMessageContains(view, view.indicators['inProgress']);
            expectMessageContains(view, view.messages['inProgress']);
            request_data[data.valueAttribute] = data.validValue;
            AjaxHelpers.expectJsonRequest(
                requests, 'PATCH', url, request_data
            );

            AjaxHelpers.respondWithNoContent(requests);
            // When server returns success.
            expectMessageContains(view, view.indicators['success']);

            view.$(data.valueElementSelector).val(data.invalidValue1).change();
            request_data[data.valueAttribute] = data.invalidValue1;
            AjaxHelpers.expectJsonRequest(
                requests, 'PATCH', url, request_data
            );
            AjaxHelpers.respondWithError(requests, 500);
            // When server returns a 500 error
            expectMessageContains(view, view.indicators['error']);
            expectMessageContains(view, view.messages['error']);

            view.$(data.valueElementSelector).val(data.invalidValue2).change();
            request_data[data.valueAttribute] = data.invalidValue2;
            AjaxHelpers.expectJsonRequest(
                requests, 'PATCH', url, request_data
            );
            AjaxHelpers.respondWithError(requests, 400, createErrorMessage(data.valueAttribute, data.validationError));
            // When server returns a validation error
            expectMessageContains(view, view.indicators['validationError']);
            expectMessageContains(view, data.validationError);
        };

        var verifyTextField = function (view, data, requests) {
            var selector = '.u-field-value > input';
            verifyEditableField(view, _.extend({
                    valueElementSelector: selector,
                }, data
            ), requests);
        }

        var verifyDropDownField = function (view, data, requests) {
            var selector = '.u-field-value > select';
            verifyEditableField(view, _.extend({
                    valueElementSelector: selector,
                }, data
            ), requests);
        }

        return {
            SELECT_OPTIONS: SELECT_OPTIONS,
            UserAccountModel: UserAccountModel,
            createFieldData: createFieldData,
            createErrorMessage: createErrorMessage,
            expectTitleAndMessageToBe: expectTitleAndMessageToBe,
            expectMessageContains: expectMessageContains,
            expectAjaxRequestWithData: expectAjaxRequestWithData,
            verifyMessageUpdates: verifyMessageUpdates,
            verifySuccessMessageReset: verifySuccessMessageReset,
            verifyEditableField: verifyEditableField,
            verifyTextField: verifyTextField,
            verifyDropDownField: verifyDropDownField
        };
    });
