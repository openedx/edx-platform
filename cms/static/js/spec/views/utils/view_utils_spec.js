define(["jquery", "underscore", "js/views/baseview", "js/views/utils/view_utils", "js/spec_helpers/edit_helpers"],
    function ($, _, BaseView, ViewUtils, view_helpers) {

        describe("ViewUtils", function() {
            describe("disabled element while running", function() {
                it("adds 'is-disabled' class to element while action is running and removes it after", function() {
                    var link,
                        deferred = new $.Deferred(),
                        promise = deferred.promise();
                    setFixtures("<a href='#' id='link'>ripe apples drop about my head</a>");
                    link = $("#link");
                    expect(link).not.toHaveClass("is-disabled");
                    ViewUtils.disableElementWhileRunning(link, function() { return promise; });
                    expect(link).toHaveClass("is-disabled");
                    deferred.resolve();
                    expect(link).not.toHaveClass("is-disabled");
                });
            });

            describe("progress notification", function() {
                it("shows progress notification and removes it upon success", function() {
                    var testMessage = "Testing...",
                        deferred = new $.Deferred(),
                        promise = deferred.promise(),
                        notificationSpy = view_helpers.createNotificationSpy();
                    ViewUtils.runOperationShowingMessage(testMessage, function() { return promise; });
                    view_helpers.verifyNotificationShowing(notificationSpy, /Testing/);
                    deferred.resolve();
                    view_helpers.verifyNotificationHidden(notificationSpy);
                });

                it("shows progress notification and leaves it showing upon failure", function() {
                    var testMessage = "Testing...",
                        deferred = new $.Deferred(),
                        promise = deferred.promise(),
                        notificationSpy = view_helpers.createNotificationSpy();
                    ViewUtils.runOperationShowingMessage(testMessage, function() { return promise; });
                    view_helpers.verifyNotificationShowing(notificationSpy, /Testing/);
                    deferred.fail();
                    view_helpers.verifyNotificationShowing(notificationSpy, /Testing/);
                });
            });
        });
    });
