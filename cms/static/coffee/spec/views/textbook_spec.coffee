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

