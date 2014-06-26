/**
 * Provides helper methods for invoking Studio modal windows in Jasmine tests.
 */
define(["jquery", "js/views/feedback_notification", "js/views/feedback_prompt"],
    function($, NotificationView, Prompt) {
        var installTemplate, installTemplates, installViewTemplates, createNotificationSpy, verifyNotificationShowing,
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

        installTemplates = function(templateNames, isFirst) {
            if (!$.isArray(templateNames)) {
                templateNames = [templateNames];
            }

            $.each(templateNames, function(index, templateName) {
                installTemplate(templateName, isFirst);
                if (isFirst) {
                    isFirst = false;
                }
            });
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

        inlineEdit = function(element, newValue) {
            var inputField;
            element.click();
            expect(element).toHaveClass('is-hidden');
            inputField = element.next().find('.xblock-field-input');
            expect(inputField).not.toHaveClass('is-hidden');
            inputField.val(newValue);
            return inputField;
        };

        verifyInlineEditChange = function(element, expectedValue, failedValue) {
            var inputField = element.next().find('.xblock-field-input');
            expect(element.text()).toBe(expectedValue);
            if (failedValue) {
                expect(element).toHaveClass('is-hidden');
                expect(inputField).not.toHaveClass('is-hidden');
            } else {
                expect(element).not.toHaveClass('is-hidden');
                expect(inputField).toHaveClass('is-hidden');
            }
        };

        return {
            'installTemplate': installTemplate,
            'installTemplates': installTemplates,
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
