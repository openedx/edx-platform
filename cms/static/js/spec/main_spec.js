(function(sandbox) {
    'use strict';
    require(["jquery", "backbone", "js/main", "edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers", "jquery.cookie"],
            function($, Backbone, main, AjaxHelpers) {
        describe("CMS", function() {
            return it("should initialize URL", function() {
                return expect(window.CMS.URL).toBeDefined();
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
                return expect(Backbone.emulateHTTP).toBeTruthy();
            });
            return it("setup AJAX CSRF token", function() {
                return expect($.ajaxSettings.headers["X-CSRFToken"]).toEqual("stubCSRFToken");
            });
        });
        describe("AJAX Errors", function() {
            var server;
            server = null;
            beforeEach(function() {
                return appendSetFixtures(sandbox({
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
                return expect($("#page-notification")).toBeEmpty();
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
                return expect($("#page-notification")).toContainElement('div.wrapper-notification-error');
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
                return expect($("#page-notification")).toBeEmpty();
            });
        });
    });

}).call(this, sandbox);  //jshint ignore:line
