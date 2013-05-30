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

describe "CMS.Views.Alert as base class", ->
    beforeEach ->
        @model = new CMS.Models.ConfirmationMessage({
            title: "Portal"
            message: "Welcome to the Aperture Science Computer-Aided Enrichment Center"
        })
        # it will be interesting to see when this.render is called, so lets spy on it
        spyOn(CMS.Views.Alert.prototype, 'render').andCallThrough()

    it "renders on initalize", ->
        view = new CMS.Views.Alert({model: @model})
        expect(view.render).toHaveBeenCalled()

    it "renders the template", ->
        view = new CMS.Views.Alert({model: @model})
        expect(view.$(".action-close")).toBeDefined()
        expect(view.$('.wrapper')).toBeShown()
        expect(view.$el).toContainText(@model.get("title"))
        expect(view.$el).toContainText(@model.get("message"))

    it "close button sends a .hide() message", ->
        spyOn(CMS.Views.Alert.prototype, 'hide').andCallThrough()

        view = new CMS.Views.Alert({model: @model})
        view.$(".action-close").click()

        expect(CMS.Views.Alert.prototype.hide).toHaveBeenCalled()
        expect(view.$('.wrapper')).toBeHiding()

describe "CMS.Views.Prompt", ->
    beforeEach ->
        @model = new CMS.Models.ConfirmationMessage({
            title: "Portal"
            message: "Welcome to the Aperture Science Computer-Aided Enrichment Center"
        })

    # for some reason, expect($("body")) blows up the test runner, so this test
    # just exercises the Prompt rather than asserting on anything. Best I can
    # do for now. :(
    it "changes class on body", ->
        # expect($("body")).not.toHaveClass("prompt-is-shown")
        view = new CMS.Views.Prompt({model: @model})
        # expect($("body")).toHaveClass("prompt-is-shown")
        view.hide()
        # expect($("body")).not.toHaveClass("prompt-is-shown")

describe "CMS.Views.Alert click events", ->
    beforeEach ->
        @model = new CMS.Models.WarningMessage(
            title: "Unsaved",
            message: "Your content is currently Unsaved.",
            actions:
                primary:
                    text: "Save",
                    class: "save-button",
                    click: jasmine.createSpy('primaryClick')
                secondary: [{
                    text: "Revert",
                    class: "cancel-button",
                    click: jasmine.createSpy('secondaryClick')
                }]

        )

        @view = new CMS.Views.Alert({model: @model})

    it "should trigger the primary event on a primary click", ->
        @view.primaryClick()
        expect(@model.get('actions').primary.click).toHaveBeenCalled()

    it "should trigger the secondary event on a secondary click", ->
        @view.secondaryClick()
        expect(@model.get('actions').secondary[0].click).toHaveBeenCalled()

    it "should apply class to primary action", ->
        expect(@view.$(".action-primary")).toHaveClass("save-button")

    it "should apply class to secondary action", ->
        expect(@view.$(".action-secondary")).toHaveClass("cancel-button")

describe "CMS.Views.Notification minShown and maxShown", ->
    beforeEach ->
        @model = new CMS.Models.SystemFeedback(
            intent: "saving"
            title: "Saving"
        )
        spyOn(CMS.Views.Notification.prototype, 'show').andCallThrough()
        spyOn(CMS.Views.Notification.prototype, 'hide').andCallThrough()
        @clock = sinon.useFakeTimers()

    afterEach ->
        @clock.restore()

    it "a minShown view should not hide too quickly", ->
        view = new CMS.Views.Notification({model: @model, minShown: 1000})
        expect(CMS.Views.Notification.prototype.show).toHaveBeenCalled()
        expect(view.$('.wrapper')).toBeShown()

        # call hide() on it, but the minShown should prevent it from hiding right away
        view.hide()
        expect(view.$('.wrapper')).toBeShown()

        # wait for the minShown timeout to expire, and check again
        @clock.tick(1001)
        expect(view.$('.wrapper')).toBeHiding()

    it "a maxShown view should hide by itself", ->
        view = new CMS.Views.Notification({model: @model, maxShown: 1000})
        expect(CMS.Views.Notification.prototype.show).toHaveBeenCalled()
        expect(view.$('.wrapper')).toBeShown()

        # wait for the maxShown timeout to expire, and check again
        @clock.tick(1001)
        expect(view.$('.wrapper')).toBeHiding()

    it "a minShown view can stay visible longer", ->
        view = new CMS.Views.Notification({model: @model, minShown: 1000})
        expect(CMS.Views.Notification.prototype.show).toHaveBeenCalled()
        expect(view.$('.wrapper')).toBeShown()

        # wait for the minShown timeout to expire, and check again
        @clock.tick(1001)
        expect(CMS.Views.Notification.prototype.hide).not.toHaveBeenCalled()
        expect(view.$('.wrapper')).toBeShown()

        # can now hide immediately
        view.hide()
        expect(view.$('.wrapper')).toBeHiding()

    it "a maxShown view can hide early", ->
        view = new CMS.Views.Notification({model: @model, maxShown: 1000})
        expect(CMS.Views.Notification.prototype.show).toHaveBeenCalled()
        expect(view.$('.wrapper')).toBeShown()

        # wait 50 milliseconds, and hide it early
        @clock.tick(50)
        view.hide()
        expect(view.$('.wrapper')).toBeHiding()

        # wait for timeout to expire, make sure it doesn't do anything weird
        @clock.tick(1000)
        expect(view.$('.wrapper')).toBeHiding()

    it "a view can have both maxShown and minShown", ->
        view = new CMS.Views.Notification({model: @model, minShown: 1000, maxShown: 2000})

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
