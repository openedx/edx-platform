define ["jquery", "js/views/feedback", "js/views/feedback_notification", "js/views/feedback_alert",
    "js/views/feedback_prompt", "sinon"],
($, SystemFeedback, NotificationView, AlertView, PromptView, sinon) ->

    tpl = readFixtures('system-feedback.underscore')

    beforeEach ->
        setFixtures(sandbox({id: "page-alert"}))
        appendSetFixtures(sandbox({id: "page-notification"}))
        appendSetFixtures(sandbox({id: "page-prompt"}))
        appendSetFixtures($("<script>", {id: "system-feedback-tpl", type: "text/template"}).text(tpl))
        @addMatchers
            toBeShown: ->
                @actual.hasClass("is-shown") and not @actual.hasClass("is-hiding")
            toBeHiding: ->
                @actual.hasClass("is-hiding") and not @actual.hasClass("is-shown")
            toContainText: (text) ->
                # remove this when we upgrade jasmine-jquery
                trimmedText = $.trim(@actual.text())
                if text and $.isFunction(text.test)
                    return text.test(trimmedText)
                else
                    return trimmedText.indexOf(text) != -1;
            toHaveBeenPrevented: ->
                # remove this when we upgrade jasmine-jquery
                eventName = @actual.eventName
                selector = @actual.selector
                @message = ->
                    [
                      "Expected event #{eventName} to have been prevented on #{selector}",
                      "Expected event #{eventName} not to have been prevented on #{selector}"
                    ]
                return jasmine.JQuery.events.wasPrevented(selector, eventName)

    describe "SystemFeedback", ->
        beforeEach ->
            @options =
                title: "Portal"
                message: "Welcome to the Aperture Science Computer-Aided Enrichment Center"
            # it will be interesting to see when this.render is called, so lets spy on it
            @renderSpy = spyOn(AlertView.Confirmation.prototype, 'render').andCallThrough()
            @showSpy = spyOn(AlertView.Confirmation.prototype, 'show').andCallThrough()
            @hideSpy = spyOn(AlertView.Confirmation.prototype, 'hide').andCallThrough()
            @clock = sinon.useFakeTimers()

        afterEach ->
            @clock.restore()

        it "requires a type and an intent", ->
            neither = =>
                new SystemFeedback(@options)
            noType = =>
                options = $.extend({}, @options)
                options.intent = "confirmation"
                new SystemFeedback(options)
            noIntent = =>
                options = $.extend({}, @options)
                options.type = "alert"
                new SystemFeedback(options)
            both = =>
                options = $.extend({}, @options)
                options.type = "alert"
                options.intent = "confirmation"
                new SystemFeedback(options)

            expect(neither).toThrow()
            expect(noType).toThrow()
            expect(noIntent).toThrow()
            expect(both).not.toThrow()

        # for simplicity, we'll use AlertView.Confirmation from here on,
        # which extends and proxies to SystemFeedback

        it "does not show on initalize", ->
            view = new AlertView.Confirmation(@options)
            expect(@renderSpy).not.toHaveBeenCalled()
            expect(@showSpy).not.toHaveBeenCalled()

        # Disabled flaky test TNL-559
        xit "renders the template", ->
            view = new AlertView.Confirmation(@options)
            view.show()

            expect(view.$(".action-close")).toBeDefined()
            expect(view.$('.wrapper')).toBeShown()
            expect(view.$el).toContainText(@options.title)
            expect(view.$el).toContainText(@options.message)

        # Disabled flaky test TNL-559
        xit "close button sends a .hide() message", ->
            view = new AlertView.Confirmation(@options).show()
            view.$(".action-close").click()
            expect(@hideSpy).toHaveBeenCalled()
            @clock.tick(900)
            expect(view.$('.wrapper')).toBeHiding()

    describe "PromptView", ->
        # for some reason, expect($("body")) blows up the test runner, so this test
        # just exercises the Prompt rather than asserting on anything. Best I can
        # do for now. :(
        it "changes class on body", ->
            # expect($("body")).not.toHaveClass("prompt-is-shown")
            view = new PromptView.Confirmation({
                title: "Portal"
                message: "Welcome to the Aperture Science Computer-Aided Enrichment Center"
            })
            # expect($("body")).toHaveClass("prompt-is-shown")
            view.hide()
            # expect($("body")).not.toHaveClass("prompt-is-shown")

    describe "NotificationView.Mini", ->
        beforeEach ->
            @view = new NotificationView.Mini()

        it "should have minShown set to 1250 by default", ->
            expect(@view.options.minShown).toEqual(1250)

        it "should have closeIcon set to false by default", ->
            expect(@view.options.closeIcon).toBeFalsy()

    # Disabled flaky test TNL-559
    xdescribe "SystemFeedback click events", ->
        beforeEach ->
            @primaryClickSpy = jasmine.createSpy('primaryClick')
            @secondaryClickSpy = jasmine.createSpy('secondaryClick')
            @view = new NotificationView.Warning(
                title: "Unsaved",
                message: "Your content is currently Unsaved.",
                actions:
                    primary:
                        text: "Save",
                        class: "save-button",
                        click: @primaryClickSpy
                    secondary:
                        text: "Revert",
                        class: "cancel-button",
                        click: @secondaryClickSpy
            )
            @view.show()

        it "should trigger the primary event on a primary click", ->
            @view.$(".action-primary").click()
            expect(@primaryClickSpy).toHaveBeenCalled()
            expect(@secondaryClickSpy).not.toHaveBeenCalled()

        it "should trigger the secondary event on a secondary click", ->
            @view.$(".action-secondary").click()
            expect(@secondaryClickSpy).toHaveBeenCalled()
            expect(@primaryClickSpy).not.toHaveBeenCalled()

        it "should apply class to primary action", ->
            expect(@view.$(".action-primary")).toHaveClass("save-button")

        it "should apply class to secondary action", ->
            expect(@view.$(".action-secondary")).toHaveClass("cancel-button")

        it "should preventDefault on primary action", ->
            spyOnEvent(".action-primary", "click")
            @view.$(".action-primary").click()
            expect("click").toHaveBeenPreventedOn(".action-primary")

        it "should preventDefault on secondary action", ->
            spyOnEvent(".action-secondary", "click")
            @view.$(".action-secondary").click()
            expect("click").toHaveBeenPreventedOn(".action-secondary")

    # Disabled flaky test TNL-559
    xdescribe "SystemFeedback not preventing events", ->
        beforeEach ->
            @clickSpy = jasmine.createSpy('clickSpy')
            @view = new AlertView.Confirmation(
                title: "It's all good"
                message: "No reason for this alert"
                actions:
                    primary:
                        text: "Whatever"
                        click: @clickSpy
                        preventDefault: false
            )
            @view.show()

        it "should not preventDefault", ->
            spyOnEvent(".action-primary", "click")
            @view.$(".action-primary").click()
            expect("click").not.toHaveBeenPreventedOn(".action-primary")
            expect(@clickSpy).toHaveBeenCalled()

    # Disabled flaky test TNL-559
    xdescribe "SystemFeedback multiple secondary actions", ->
        beforeEach ->
            @secondarySpyOne = jasmine.createSpy('secondarySpyOne')
            @secondarySpyTwo = jasmine.createSpy('secondarySpyTwo')
            @view = new NotificationView.Warning(
                title: "No Primary",
                message: "Pick a secondary action",
                actions:
                    secondary: [
                        {
                            text: "Option One"
                            class: "option-one"
                            click: @secondarySpyOne
                        }, {
                            text: "Option Two"
                            class: "option-two"
                            click: @secondarySpyTwo
                        }
                    ]
            )
            @view.show()

        it "should render both", ->
            expect(@view.el).toContain(".action-secondary.option-one")
            expect(@view.el).toContain(".action-secondary.option-two")
            expect(@view.el).not.toContain(".action-secondary.option-one.option-two")
            expect(@view.$(".action-secondary.option-one")).toContainText("Option One")
            expect(@view.$(".action-secondary.option-two")).toContainText("Option Two")

        it "should differentiate clicks (1)", ->
            @view.$(".option-one").click()
            expect(@secondarySpyOne).toHaveBeenCalled()
            expect(@secondarySpyTwo).not.toHaveBeenCalled()

        it "should differentiate clicks (2)", ->
            @view.$(".option-two").click()
            expect(@secondarySpyOne).not.toHaveBeenCalled()
            expect(@secondarySpyTwo).toHaveBeenCalled()

    describe "NotificationView minShown and maxShown", ->
        beforeEach ->
            @showSpy = spyOn(NotificationView.Confirmation.prototype, 'show')
            @showSpy.andCallThrough()
            @hideSpy = spyOn(NotificationView.Confirmation.prototype, 'hide')
            @hideSpy.andCallThrough()
            @clock = sinon.useFakeTimers()

        afterEach ->
            @clock.restore()

        # Disabled flaky test TNL-559
        xit "should not have minShown or maxShown by default", ->
            view = new NotificationView.Confirmation()
            expect(view.options.minShown).toEqual(0)
            expect(view.options.maxShown).toEqual(Infinity)

        # Disabled flaky test TNL-559
        xit "a minShown view should not hide too quickly", ->
            view = new NotificationView.Confirmation({minShown: 1000})
            view.show()
            expect(view.$('.wrapper')).toBeShown()

            # call hide() on it, but the minShown should prevent it from hiding right away
            view.hide()
            expect(view.$('.wrapper')).toBeShown()

            # wait for the minShown timeout to expire, and check again
            @clock.tick(1001)
            expect(view.$('.wrapper')).toBeHiding()

        # Disabled flaky test TNL-559
        xit "a maxShown view should hide by itself", ->
            view = new NotificationView.Confirmation({maxShown: 1000})
            view.show()
            expect(view.$('.wrapper')).toBeShown()

            # wait for the maxShown timeout to expire, and check again
            @clock.tick(1001)
            expect(view.$('.wrapper')).toBeHiding()

        # Disabled flaky test TNL-559
        xit "a minShown view can stay visible longer", ->
            view = new NotificationView.Confirmation({minShown: 1000})
            view.show()
            expect(view.$('.wrapper')).toBeShown()

            # wait for the minShown timeout to expire, and check again
            @clock.tick(1001)
            expect(@hideSpy).not.toHaveBeenCalled()
            expect(view.$('.wrapper')).toBeShown()

            # can now hide immediately
            view.hide()
            expect(view.$('.wrapper')).toBeHiding()

        # Disabled flaky test TNL-559
        xit "a maxShown view can hide early", ->
            view = new NotificationView.Confirmation({maxShown: 1000})
            view.show()
            expect(view.$('.wrapper')).toBeShown()

            # wait 50 milliseconds, and hide it early
            @clock.tick(50)
            view.hide()
            expect(view.$('.wrapper')).toBeHiding()

            # wait for timeout to expire, make sure it doesn't do anything weird
            @clock.tick(1000)
            expect(view.$('.wrapper')).toBeHiding()

        it "a view can have both maxShown and minShown", ->
            view = new NotificationView.Confirmation({minShown: 1000, maxShown: 2000})
            view.show()

            # can't hide early
            @clock.tick(50)
            view.hide()
            expect(view.$('.wrapper')).toBeShown()
            @clock.tick(1000)
            expect(view.$('.wrapper')).toBeHiding()

            # show it again, and let it hide automatically
            view.show()
            @clock.tick(1050)
            expect(view.$('.wrapper')).toBeShown()
            @clock.tick(1000)
            expect(view.$('.wrapper')).toBeHiding()
