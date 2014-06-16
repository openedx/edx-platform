/**
 * Provides helper methods for invoking Studio modal windows in Jasmine tests.
 */
define(["jquery", "js/views/feedback_notification", "js/spec_helpers/create_sinon"],
    function($, NotificationView, create_sinon) {
        var installTemplate, installTemplates, installViewTemplates, createNotificationSpy,
            verifyNotificationShowing, verifyNotificationHidden;

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

        return {
            'installTemplate': installTemplate,
            'installTemplates': installTemplates,
            'installViewTemplates': installViewTemplates,
            'createNotificationSpy': createNotificationSpy,
            'verifyNotificationShowing': verifyNotificationShowing,
            'verifyNotificationHidden': verifyNotificationHidden
        };
    });
