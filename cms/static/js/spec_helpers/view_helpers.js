/**
 * Provides helper methods for invoking Studio modal windows in Jasmine tests.
 */
define(['jquery', 'js/views/feedback_notification', 'js/views/feedback_prompt'],
    function($, NotificationView, Prompt) {
        'use strict';
        var installTemplate, installTemplates, installViewTemplates, createFeedbackSpy, verifyFeedbackShowing,
            verifyFeedbackHidden, createNotificationSpy, verifyNotificationShowing,
            verifyNotificationHidden, createPromptSpy, confirmPrompt, verifyPromptShowing,
            verifyPromptHidden;

        installTemplate = function(templateName, isFirst) {
            var template = readFixtures(templateName + '.underscore'),
                templateId = templateName + '-tpl';

            if (isFirst) {
                setFixtures($('<script>', { id: templateId, type: 'text/template' }).text(template));
            } else {
                appendSetFixtures($('<script>', { id: templateId, type: 'text/template' }).text(template));
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

        return {
            'installTemplate': installTemplate,
            'installTemplates': installTemplates,
            'installViewTemplates': installViewTemplates,
            'createNotificationSpy': createNotificationSpy,
            'verifyNotificationShowing': verifyNotificationShowing,
            'verifyNotificationHidden': verifyNotificationHidden,
            'confirmPrompt': confirmPrompt,
            'createPromptSpy': createPromptSpy,
            'verifyPromptShowing': verifyPromptShowing,
            'verifyPromptHidden': verifyPromptHidden
        };
    });
