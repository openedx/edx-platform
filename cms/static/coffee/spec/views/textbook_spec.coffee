feedbackTpl = readFixtures('system-feedback.underscore')

beforeEach ->
    # remove this when we upgrade jasmine-jquery
    @addMatchers
        toContainText: (text) ->
            trimmedText = $.trim(@actual.text())
            if text and $.isFunction(text.test)
                return text.test(trimmedText)
            else
                return trimmedText.indexOf(text) != -1;

describe "CMS.Views.TextbookShow", ->
    describe "Basic", ->
        tpl = readFixtures('textbook-show.underscore')

        beforeEach ->
            setFixtures($("<script>", {id: "show-textbook-tpl", type: "text/template"}).text(tpl))
            appendSetFixtures($("<script>", {id: "system-feedback-tpl", type: "text/template"}).text(feedbackTpl))
            appendSetFixtures(sandbox({id: "page-notification"}))
            appendSetFixtures(sandbox({id: "page-prompt"}))
            @model = new CMS.Models.Textbook({name: "Life Sciences"})
            @collection = new CMS.Collections.TextbookSet()
            spyOn(@collection, 'save')
            @collection.add(@model)
            @view = new CMS.Views.TextbookShow({model: @model})

        it "should render properly", ->
            @view.render()
            expect(@view.$el).toContainText("Life Sciences")

        it "should trigger an editOne event on the collection when the edit button is clicked", ->
            spyOn(@collection, "trigger").andCallThrough()
            @view.render().$(".edit").click()
            expect(@collection.trigger).toHaveBeenCalledWith("editOne", @model)
            expect(@collection.editing).toEqual(@model)

        it "should pop a delete confirmation when the delete button is clicked", ->
            promptSpies = spyOnConstructor(CMS.Views, "Prompt")
            @view.render().$(".delete").click()
            expect(promptSpies.constructor).toHaveBeenCalled()
            msg = promptSpies.constructor.mostRecentCall.args[0].model
            expect(msg.get("title")).toMatch(/Life Sciences/)
            # hasn't actually been removed
            expect(@collection).toContain(@model)
            expect(@collection.save).not.toHaveBeenCalled()
            # run the primary function to indicate confirmation
            view = jasmine.createSpyObj('view', ['hide'])
            msg.get("actions").primary.click.call(msg, view)
            # now it's been removed
            expect(@collection).not.toContain(@model)
            expect(@collection.save).toHaveBeenCalled()

        it "should show chapters appropriately", ->
            @model.get("chapters").add([{}, {}, {}])
            @model.set('showChapters', false)
            @view.render().$(".show-chapters").click()
            expect(@model.get('showChapters')).toBeTruthy()

        it "should hide chapters appropriately", ->
            @model.get("chapters").add([{}, {}, {}])
            @model.set('showChapters', true)
            @view.render().$(".hide-chapters").click()
            expect(@model.get('showChapters')).toBeFalsy()



describe "CMS.Views.TextbookEdit", ->
    describe "Basic", ->
        tpl = readFixtures('textbook-edit.underscore')
        chapterTpl = readFixtures('chapter.underscore')

        beforeEach ->
            setFixtures($("<script>", {id: "new-textbook-tpl", type: "text/template"}).text(tpl))
            appendSetFixtures($("<script>", {id: "new-chapter-tpl", type: "text/template"}).text(chapterTpl))
            appendSetFixtures($("<script>", {id: "system-feedback-tpl", type: "text/template"}).text(feedbackTpl))
            appendSetFixtures(sandbox({id: "page-notification"}))
            appendSetFixtures(sandbox({id: "page-prompt"}))
            @model = new CMS.Models.Textbook({name: "Life Sciences"})
            @collection = new CMS.Collections.TextbookSet()
            spyOn(@collection, 'save')
            @collection.add(@model)
            @collection.editing = @model
            @view = new CMS.Views.TextbookEdit({model: @model})
            spyOn(@view, 'render').andCallThrough()

        it "should render properly", ->
            @view.render()
            expect(@view.$("input[name=textbook-name]").val()).toEqual("Life Sciences")

        it "should allow you to create new chapters", ->
            numChapters = @model.get("chapters").length
            @view.render().$(".action-add-chapter").click()
            expect(@model.get("chapters").length).toEqual(numChapters+1)

        it "should save properly", ->
            @view.render()
            @view.$("input[name=textbook-name]").val("starfish")
            @view.$("input[name=chapter1-name]").val("foobar")
            @view.$("form").submit()
            expect(@model.get("name")).toEqual("starfish")
            expect(@model.get("chapters").at(0).get("name")).toEqual("foobar")
            expect(@collection.save).toHaveBeenCalled()

        it "does not save on cancel", ->
            @view.render()
            @view.$("input[name=textbook-name]").val("starfish")
            @view.$("input[name=chapter1-name]").val("foobar")
            @view.$(".action-cancel").click()
            expect(@model.get("name")).not.toEqual("starfish")
            expect(@model.get("chapters").at(0).get("name")).not.toEqual("foobar")
            expect(@collection.save).not.toHaveBeenCalled()
            expect(@collection.editing).toBeUndefined()


describe "CMS.Views.ListTextbooks", ->
    noTextbooksTpl = readFixtures("no-textbooks.underscore")

    beforeEach ->
        setFixtures($("<script>", {id: "no-textbooks-tpl", type: "text/template"}).text(noTextbooksTpl))
        @showSpies = spyOnConstructor(CMS.Views, "TextbookShow", ["render"])
        @showSpies.render.andReturn(@showSpies) # equivalent of `return this`
        showEl = $("<li>")
        @showSpies.$el = showEl
        @showSpies.el = showEl.get(0)
        @editSpies = spyOnConstructor(CMS.Views, "TextbookEdit", ["render"])
        editEl = $("<li>")
        @editSpies.render.andReturn(@editSpies)
        @editSpies.$el = editEl
        @editSpies.el= editEl.get(0)

        @collection = new CMS.Collections.TextbookSet
        @view = new CMS.Views.ListTextbooks({collection: @collection})
        @view.render()
        @showSpies.constructor.reset()
        @editSpies.constructor.reset()

    it "should render the empty template if there are no textbooks", ->
        expect(@view.$el).toContainText("You haven't added any textbooks to this course yet")
        expect(@view.$el).toContain(".new-button")

    it "should render TextbookShow views by default if no textbook is being edited", ->
        # add three empty textbooks to the collection
        @collection.add([{}, {}, {}])
        # reset spies due to re-rendering on collection modification
        @showSpies.constructor.reset()
        @editSpies.constructor.reset()
        # render once and test
        @view.render()

        expect(@view.$el).not.toContainText(
            "You haven't added any textbooks to this course yet")
        expect(@view.$el).toBe("ul")
        expect(@showSpies.constructor).toHaveBeenCalled()
        expect(@showSpies.constructor.calls.length).toEqual(3);
        expect(@editSpies.constructor).not.toHaveBeenCalled()

    it "should render a TextbookEdit view for a textbook being edited", ->
        # add three empty textbooks to the collection
        @collection.add([{}, {}, {}])
        # mark the second one as being edited
        editing = @collection.at(1)
        @collection.trigger('editOne', editing)
        # reset spies
        @showSpies.constructor.reset()
        @editSpies.constructor.reset()
        # render once and test
        @view.render()

        expect(@showSpies.constructor).toHaveBeenCalled()
        expect(@showSpies.constructor.calls.length).toEqual(2)
        expect(@showSpies.constructor).not.toHaveBeenCalledWith({model: editing})
        expect(@editSpies.constructor).toHaveBeenCalled()
        expect(@editSpies.constructor.calls.length).toEqual(1)
        expect(@editSpies.constructor).toHaveBeenCalledWith({model: editing})

    it "should add a new textbook when the new-button is clicked", ->
        @view.$(".new-button").click()

        expect(@collection.length).toEqual(1)
        expect(@collection.editing).toBeDefined()
        editing = @collection.editing
        expect(editing).toEqual(@collection.at(0))
        expect(@editSpies.constructor).toHaveBeenCalledWith({model: editing})
        expect(@view.$el).toContain(@editSpies.$el)
        expect(@view.$el).not.toContain(@showSpies.$el)


