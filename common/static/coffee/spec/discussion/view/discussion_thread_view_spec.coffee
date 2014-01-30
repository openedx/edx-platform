describe "DiscussionThreadView", ->
    beforeEach ->
        setFixtures(
            """
            <script type="text/template" id="thread-template">
                <article class="discussion-article">
                    <div class="response-count"/> 
                    <ol class="responses"/>
                    <div class="response-pagination"/>
                </article>
            </script>
            <div class="thread-fixture"/>
            """
        )

        jasmine.Clock.useMock()
        @threadData = {
            id: "dummy"
        }
        @thread = new Thread(@threadData)
        @view = new DiscussionThreadView({ model: @thread })
        @view.setElement($(".thread-fixture"))
        spyOn($, "ajax")
        # Avoid unnecessary boilerplate
        spyOn(@view.showView, "render")
        spyOn(@view, "makeWmdEditor")
        spyOn(DiscussionThreadView.prototype, "renderResponse")

    describe "response count and pagination", ->

        setNextResponseContent = (content) ->
            $.ajax.andCallFake(
                (params) =>
                    params.success({"content": content})
                    {always: ->}
            )

        renderWithContent = (view, content) ->
            setNextResponseContent(content)
            view.render()
            jasmine.Clock.tick(100)

        assertRenderedCorrectly = (view, countText, displayCountText, buttonText) ->
            expect(view.$el.find(".response-count").text()).toEqual(countText)
            if displayCountText
                expect(view.$el.find(".response-display-count").text()).toEqual(displayCountText)
            else
                expect(view.$el.find(".response-display-count").length).toEqual(0)
            if buttonText
                expect(view.$el.find(".load-response-button").text()).toEqual(buttonText)
            else
                expect(view.$el.find(".load-response-button").length).toEqual(0)

        it "correctly render for a thread with no responses", ->
            renderWithContent(@view, {resp_total: 0, children: []})
            assertRenderedCorrectly(@view, "0 responses", null, null)

        it "correctly render for a thread with one response", ->
            renderWithContent(@view, {resp_total: 1, children: [{}]})
            assertRenderedCorrectly(@view, "1 response", "Showing all responses", null)

        it "correctly render for a thread with one additional page", ->
            renderWithContent(@view, {resp_total: 2, children: [{}]})
            assertRenderedCorrectly(@view, "2 responses", "Showing first response", "Load all responses")

        it "correctly render for a thread with multiple additional pages", ->
            renderWithContent(@view, {resp_total: 111, children: [{}, {}]})
            assertRenderedCorrectly(@view, "111 responses", "Showing first 2 responses", "Load next 100 responses")

        describe "on clicking the load more button", ->
            beforeEach ->
                renderWithContent(@view, {resp_total: 5, children: [{}]})
                assertRenderedCorrectly(@view, "5 responses", "Showing first response", "Load all responses")
                
            it "correctly re-render when all threads have loaded", ->
                setNextResponseContent({resp_total: 5, children: [{}, {}, {}, {}]})
                @view.$el.find(".load-response-button").click()
                assertRenderedCorrectly(@view, "5 responses", "Showing all responses", null)

            it "correctly re-render when one page remains", ->
                setNextResponseContent({resp_total: 42, children: [{}, {}]})
                @view.$el.find(".load-response-button").click()
                assertRenderedCorrectly(@view, "42 responses", "Showing first 3 responses", "Load all responses")

            it "correctly re-render when multiple pages remain", ->
                setNextResponseContent({resp_total: 111, children: [{}, {}]})
                @view.$el.find(".load-response-button").click()
                assertRenderedCorrectly(@view, "111 responses", "Showing first 3 responses", "Load next 100 responses")
