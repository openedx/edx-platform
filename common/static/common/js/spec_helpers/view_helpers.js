/**
 * Provides helper methods for invoking Studio modal windows in Jasmine tests.
 */
;(function (define) {
    'use strict';
define(["jquery", "common/js/components/views/feedback_notification", "common/js/components/views/feedback_prompt",
        'common/js/spec_helpers/ajax_helpers'],
    function($, NotificationView, Prompt, AjaxHelpers) {
        var installViewTemplates, createFeedbackSpy, verifyFeedbackShowing,
            verifyFeedbackHidden, createNotificationSpy, verifyNotificationShowing,
            verifyNotificationHidden, createPromptSpy, confirmPrompt, inlineEdit, verifyInlineEditChange,
            installMockAnalytics, removeMockAnalytics, verifyPromptShowing, verifyPromptHidden,
            clickDeleteItem, patchAndVerifyRequest, submitAndVerifyFormSuccess, submitAndVerifyFormError,
            verifyElementInFocus, verifyElementNotInFocus;

        installViewTemplates = function() {
            appendSetFixtures('<div id="page-notification"></div>');
        };

        createFeedbackSpy = function(type, intent) {
            var feedbackSpy = spyOnConstructor(type, intent, ['show', 'hide']);
            feedbackSpy.show.andReturn(feedbackSpy);
            return feedbackSpy;
        };

        verifyFeedbackShowing = function(feedbackSpy, text) {
            var options;
            expect(feedbackSpy.constructor).toHaveBeenCalled();
            expect(feedbackSpy.show).toHaveBeenCalled();
            expect(feedbackSpy.hide).not.toHaveBeenCalled();
            options = feedbackSpy.constructor.mostRecentCall.args[0];
            expect(options.title).toMatch(text);
        };

        verifyFeedbackHidden = function(feedbackSpy) {
            expect(feedbackSpy.hide).toHaveBeenCalled();
        };

        createNotificationSpy = function(type) {
            return createFeedbackSpy(NotificationView, type || 'Mini');
        };

        verifyNotificationShowing = function(notificationSpy, text) {
            verifyFeedbackShowing.apply(this, arguments);
        };

        verifyNotificationHidden = function(notificationSpy) {
            verifyFeedbackHidden.apply(this, arguments);
        };

        createPromptSpy = function(type) {
            return createFeedbackSpy(Prompt, type || 'Warning');
        };

        confirmPrompt = function(promptSpy, pressSecondaryButton) {
            expect(promptSpy.constructor).toHaveBeenCalled();
            if (pressSecondaryButton) {
                promptSpy.constructor.mostRecentCall.args[0].actions.secondary.click(promptSpy);
            } else {
                promptSpy.constructor.mostRecentCall.args[0].actions.primary.click(promptSpy);
            }
        };

        verifyPromptShowing = function(promptSpy, text) {
            verifyFeedbackShowing.apply(this, arguments);
        };

        verifyPromptHidden = function(promptSpy) {
            verifyFeedbackHidden.apply(this, arguments);
        };

        installMockAnalytics = function() {
            window.analytics = jasmine.createSpyObj('analytics', ['track']);
            window.course_location_analytics = jasmine.createSpy();
        };

        removeMockAnalytics = function() {
            delete window.analytics;
            delete window.course_location_analytics;
        };

        inlineEdit = function(editorWrapper, newValue) {
            var inputField = editorWrapper.find('.xblock-field-input'),
                editButton = editorWrapper.find('.xblock-field-value-edit');
            editButton.click();
            expect(editorWrapper).toHaveClass('is-editing');
            inputField.val(newValue);
            return inputField;
        };

        verifyInlineEditChange = function(editorWrapper, expectedValue, failedValue) {
            var displayName = editorWrapper.find('.xblock-field-value');
            expect(displayName.text()).toBe(expectedValue);
            if (failedValue) {
                expect(editorWrapper).toHaveClass('is-editing');
            } else {
                expect(editorWrapper).not.toHaveClass('is-editing');
            }
        };

        clickDeleteItem = function (that, promptSpy, promptText) {
            that.view.$('.delete').click();
            verifyPromptShowing(promptSpy, promptText);
            confirmPrompt(promptSpy);
            verifyPromptHidden(promptSpy);
        };

        patchAndVerifyRequest = function (requests, url, notificationSpy) {
            // Backbone.emulateHTTP is enabled in our system, so setting this
            // option  will fake PUT, PATCH and DELETE requests with a HTTP POST,
            // setting the X-HTTP-Method-Override header with the true method.
            AjaxHelpers.expectJsonRequest(requests, 'POST', url);
            expect(_.last(requests).requestHeaders['X-HTTP-Method-Override']).toBe('DELETE');
            verifyNotificationShowing(notificationSpy, /Deleting/);
        };

        submitAndVerifyFormSuccess = function (view, requests, notificationSpy) {
            view.$('form').submit();
            verifyNotificationShowing(notificationSpy, /Saving/);
            AjaxHelpers.respondWithJson(requests, {});
            verifyNotificationHidden(notificationSpy);
        };

        submitAndVerifyFormError = function (view, requests, notificationSpy) {
            view.$('form').submit();
            verifyNotificationShowing(notificationSpy, /Saving/);
            AjaxHelpers.respondWithError(requests);
            verifyNotificationShowing(notificationSpy, /Saving/);
        };

        verifyElementInFocus = function(view, selector) {
            waitsFor(
              function() { return view.$(selector + ':focus').length === 1; },
              "element to have focus: " + selector,
              500
            );
        };

        verifyElementNotInFocus = function(view, selector) {
            waitsFor(
              function() { return view.$(selector + ':focus').length === 0; },
              "element to not have focus: " + selector,
              500
            );
        };

        return {
            'installViewTemplates': installViewTemplates,
            'createNotificationSpy': createNotificationSpy,
            'verifyNotificationShowing': verifyNotificationShowing,
            'verifyNotificationHidden': verifyNotificationHidden,
            'confirmPrompt': confirmPrompt,
            'createPromptSpy': createPromptSpy,
            'verifyPromptShowing': verifyPromptShowing,
            'verifyPromptHidden': verifyPromptHidden,
            'inlineEdit': inlineEdit,
            'verifyInlineEditChange': verifyInlineEditChange,
            'installMockAnalytics': installMockAnalytics,
            'removeMockAnalytics': removeMockAnalytics,
            'clickDeleteItem': clickDeleteItem,
            'patchAndVerifyRequest': patchAndVerifyRequest,
            'submitAndVerifyFormSuccess': submitAndVerifyFormSuccess,
            'submitAndVerifyFormError': submitAndVerifyFormError,
            'verifyElementInFocus': verifyElementInFocus,
            'verifyElementNotInFocus': verifyElementNotInFocus
        };
    });
}).call(this, define || RequireJS.define);
