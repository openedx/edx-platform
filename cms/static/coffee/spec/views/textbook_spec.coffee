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
