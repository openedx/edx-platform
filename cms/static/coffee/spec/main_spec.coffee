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

        it "setup AJAX CSRF token", ->
            expect($.ajaxSettings.headers["X-CSRFToken"]).toEqual("stubCSRFToken")

    describe "AJAX Errors", ->
        tpl = readFixtures('system-feedback.underscore')

        beforeEach ->
            setFixtures($("<script>", {id: "system-feedback-tpl", type: "text/template"}).text(tpl))
            appendSetFixtures(sandbox({id: "page-notification"}))

        it "successful AJAX request does not pop an error notification", ->
            server = AjaxHelpers['server'](200, this)

            expect($("#page-notification")).toBeEmpty()
            $.ajax("/test")
            expect($("#page-notification")).toBeEmpty()
            server.respond()
            expect($("#page-notification")).toBeEmpty()

        it "AJAX request with error should pop an error notification", ->
            server = AjaxHelpers['server'](500, this)

            $.ajax("/test")
            server.respond()
            expect($("#page-notification")).not.toBeEmpty()
            expect($("#page-notification")).toContain('div.wrapper-notification-error')

        it "can override AJAX request with error so it does not pop an error notification", ->
            server = AjaxHelpers['server'](500, this)

            $.ajax
                url: "/test"
                notifyOnError: false

            server.respond()
            expect($("#page-notification")).toBeEmpty()
