/**
 * Provides helper methods for invoking Studio modal windows in Jasmine tests.
 */
define(["jquery", "js/views/feedback_notification", "js/views/feedback_prompt"],
    function($, NotificationView, Prompt) {
        var installTemplate, installViewTemplates, createNotificationSpy, verifyNotificationShowing,
            verifyNotificationHidden, createPromptSpy, confirmPrompt, inlineEdit, verifyInlineEditChange,
            installMockAnalytics, removeMockAnalytics;

        installTemplate = function(templateName, isFirst, templateId) {
            var template = readFixtures(templateName + '.underscore');
            if (!templateId) {
                templateId = templateName + '-tpl';
            }
            if (isFirst) {
                setFixtures($("<script>", { id: templateId, type: "text/template" }).text(template));
            } else {
                appendSetFixtures($("<script>", { id: templateId, type: "text/template" }).text(template));
            }
        };

        installViewTemplates = function(append) {
            installTemplate('system-feedback', !append);
            appendSetFixtures('<div id="page-notification"></div>');
        };

        createNotificationSpy = function(type) {
            var notificationSpy = spyOnConstructor(NotificationView, type || "Mini", ["show", "hide"]);
            notificationSpy.show.andReturn(notificationSpy);
            return notificationSpy;
        };

        verifyNotificationShowing = function(notificationSpy, text) {
            expect(notificationSpy.constructor).toHaveBeenCalled();
            expect(notificationSpy.show).toHaveBeenCalled();
            expect(notificationSpy.hide).not.toHaveBeenCalled();
            var options = notificationSpy.constructor.mostRecentCall.args[0];
            expect(options.title).toMatch(text);
        };

        verifyNotificationHidden = function(notificationSpy) {
            expect(notificationSpy.hide).toHaveBeenCalled();
        };

        createPromptSpy = function() {
            var promptSpy = spyOnConstructor(Prompt, "Warning", ["show", "hide"]);
            promptSpy.show.andReturn(this.promptSpies);
            return promptSpy;
        };

        confirmPrompt = function(promptSpy, pressSecondaryButton) {
            expect(promptSpy.constructor).toHaveBeenCalled();
            if (pressSecondaryButton) {
                promptSpy.constructor.mostRecentCall.args[0].actions.secondary.click(promptSpy);
            } else {
                promptSpy.constructor.mostRecentCall.args[0].actions.primary.click(promptSpy);
            }
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
            'installTemplate': installTemplate,
            'installViewTemplates': installViewTemplates,
            'createNotificationSpy': createNotificationSpy,
            'verifyNotificationShowing': verifyNotificationShowing,
            'verifyNotificationHidden': verifyNotificationHidden,
            'createPromptSpy': createPromptSpy,
            'confirmPrompt': confirmPrompt,
            'inlineEdit': inlineEdit,
            'verifyInlineEditChange': verifyInlineEditChange,
            'installMockAnalytics': installMockAnalytics,
            'removeMockAnalytics': removeMockAnalytics
        };
    });
