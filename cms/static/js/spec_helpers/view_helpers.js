/**
 * Provides helper methods for invoking Studio modal windows in Jasmine tests.
 */
define(["jquery", "js/views/feedback_notification", "js/spec_helpers/create_sinon"],
    function($, NotificationView, create_sinon) {
        var installTemplate, installViewTemplates, createNotificationSpy, verifyNotificationShowing,
            verifyNotificationHidden;

        installTemplate = function(templateName, isFirst) {
            var template = readFixtures(templateName + '.underscore'),
                templateId = templateName + '-tpl';
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

        return {
            'installTemplate': installTemplate,
            'installViewTemplates': installViewTemplates,
            'createNotificationSpy': createNotificationSpy,
            'verifyNotificationShowing': verifyNotificationShowing,
            'verifyNotificationHidden': verifyNotificationHidden
        };
    });
