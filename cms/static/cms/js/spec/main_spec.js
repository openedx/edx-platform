/* globals sandbox */

(function(sandbox) {
    'use strict';
    require(["jquery", "backbone", "cms/js/main", "edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers", "jquery.cookie"],
            function($, Backbone, main, AjaxHelpers) {
        describe("CMS", function() {
            it("should initialize URL", function() {
                expect(window.CMS.URL).toBeDefined();
            });
        });
        describe("main helper", function() {
            beforeEach(function() {
                this.previousAjaxSettings = $.extend(true, {}, $.ajaxSettings);
                spyOn($, "cookie").and.callFake(function(param) {
                    if (param === "csrftoken") {
                        return "stubCSRFToken";
                    }
                });
                return main();
            });
            afterEach(function() {
                $.ajaxSettings = this.previousAjaxSettings;
                return $.ajaxSettings;
            });
            it("turn on Backbone emulateHTTP", function() {
                expect(Backbone.emulateHTTP).toBeTruthy();
            });
            it("setup AJAX CSRF token", function() {
                expect($.ajaxSettings.headers["X-CSRFToken"]).toEqual("stubCSRFToken");
            });
        });
        describe("AJAX Errors", function() {
            var server;
            server = null;
            beforeEach(function() {
                appendSetFixtures(sandbox({
                    id: "page-notification"
                }));
            });
            afterEach(function() {
                return server && server.restore();
            });
            it("successful AJAX request does not pop an error notification", function() {
                server = AjaxHelpers.server([
                    200, {
                        "Content-Type": "application/json"
                    }, "{}"
                ]);
                expect($("#page-notification")).toBeEmpty();
                $.ajax("/test");
                expect($("#page-notification")).toBeEmpty();
                server.respond();
                expect($("#page-notification")).toBeEmpty();
            });
            it("AJAX request with error should pop an error notification", function() {
                server = AjaxHelpers.server([
                    500, {
                        "Content-Type": "application/json"
                    }, "{}"
                ]);
                $.ajax("/test");
                server.respond();
                expect($("#page-notification")).not.toBeEmpty();
                expect($("#page-notification")).toContainElement('div.wrapper-notification-error');
            });
            it("can override AJAX request with error so it does not pop an error notification", function() {
                server = AjaxHelpers.server([
                    500, {
                        "Content-Type": "application/json"
                    }, "{}"
                ]);
                $.ajax({
                    url: "/test",
                    notifyOnError: false
                });
                server.respond();
                expect($("#page-notification")).toBeEmpty();
            });
        });
    });
}).call(this, sandbox);
