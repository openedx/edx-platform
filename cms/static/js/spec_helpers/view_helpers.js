/**
 * Provides helper methods for invoking Studio modal windows in Jasmine tests.
 */
define(["jquery", "js/views/feedback_notification", "js/views/feedback_prompt", "js/common_helpers/template_helpers"],
    function($, NotificationView, Prompt, TemplateHelpers) {
        var installViewTemplates, createFeedbackSpy, verifyFeedbackShowing,
            verifyFeedbackHidden, createNotificationSpy, verifyNotificationShowing,
            verifyNotificationHidden, createPromptSpy, confirmPrompt, inlineEdit, verifyInlineEditChange,
            installMockAnalytics, removeMockAnalytics, verifyPromptShowing, verifyPromptHidden;

        installViewTemplates = function(append) {
            TemplateHelpers.installTemplate('system-feedback', !append);
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
            'removeMockAnalytics': removeMockAnalytics
        };
    });
