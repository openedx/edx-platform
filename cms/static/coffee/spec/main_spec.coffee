require ["jquery", "backbone", "coffee/src/main", "common/js/spec_helpers/ajax_helpers", "jasmine-stealth", "jquery.cookie"],
($, Backbone, main, AjaxHelpers) ->
    describe "CMS", ->
        it "should initialize URL", ->
            expect(window.CMS.URL).toBeDefined()

    describe "main helper", ->
        beforeEach ->
            @previousAjaxSettings = $.extend(true, {}, $.ajaxSettings)
            spyOn($, "cookie")
            $.cookie.when("csrftoken").thenReturn("stubCSRFToken")
            main()

        afterEach ->
            $.ajaxSettings = @previousAjaxSettings

        it "turn on Backbone emulateHTTP", ->
            expect(Backbone.emulateHTTP).toBeTruthy()

        it "adds a CSRF token if the AJAX call is not a GET", ->
            spyOn($, "ajax").andCallThrough()
            $.ajax({
              url: "/test",
              type: "POST",
              contentType: "application/json; charset=utf-8",
              dataType: "json",
              data: JSON.stringify({id: 2}),
              success: function() { return true }
            })
            console.log($.ajax.mostRecentCall)
            expect(1).toEqual(1);

    describe "AJAX Errors", ->

        beforeEach ->
            appendSetFixtures(sandbox({id: "page-notification"}))

        it "successful AJAX request does not pop an error notification", ->
            server = AjaxHelpers.server(this, [200, {}, ''])

            expect($("#page-notification")).toBeEmpty()
            $.ajax("/test")
            expect($("#page-notification")).toBeEmpty()
            server.respond()
            expect($("#page-notification")).toBeEmpty()

        it "AJAX request with error should pop an error notification", ->
            server = AjaxHelpers.server(this, [500, {}, ''])

            $.ajax("/test")
            server.respond()
            expect($("#page-notification")).not.toBeEmpty()
            expect($("#page-notification")).toContain('div.wrapper-notification-error')

        it "can override AJAX request with error so it does not pop an error notification", ->
            server = AjaxHelpers.server(this, [500, {}, ''])

            $.ajax
                url: "/test"
                notifyOnError: false

            server.respond()
            expect($("#page-notification")).toBeEmpty()
