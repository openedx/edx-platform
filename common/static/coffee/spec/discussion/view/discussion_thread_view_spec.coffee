describe "DiscussionThreadView", ->
    beforeEach ->
        setFixtures(
            """
            <script type="text/template" id="thread-template">
                <article class="discussion-article">
                    <div class="thread-content-wrapper"></div>
                    <div class="post-extended-content">
                        <div class="response-count"></div>
                        <ol class="responses"></ol>
                        <div class="response-pagination"></div>
                    </div>
                    <div class="post-tools">
                        <a href="javascript:void(0)" class="forum-thread-expand">Expand</a>
                        <a href="javascript:void(0)" class="forum-thread-collapse">Collapse</a>
                    </div>
                </article>
            </script>
            <script type="text/template" id="thread-show-template">
                <div class="discussion-post">
                    <div class="post-body"><%- body %></div>
                </div>
            </script>
            <div class="thread-fixture"/>
            """
        )

        jasmine.Clock.useMock()
        @threadData = DiscussionViewSpecHelper.makeThreadWithProps({})
        @thread = new Thread(@threadData)
        spyOn($, "ajax")
        # Avoid unnecessary boilerplate
        spyOn(DiscussionThreadShowView.prototype, "convertMath")
        spyOn(DiscussionContentView.prototype, "makeWmdEditor")
        spyOn(DiscussionThreadView.prototype, "renderResponse")

    assertContentVisible = (view, selector, visible) ->
        content = view.$el.find(selector)
        expect(content.length).toBeGreaterThan(0)
        content.each (i, elem) ->
            expect($(elem).is(":visible")).toEqual(visible)

    assertExpandedContentVisible = (view, expanded) ->
        expect(view.$el.hasClass("expanded")).toEqual(expanded)
        assertContentVisible(view, ".post-extended-content", expanded)
        assertContentVisible(view, ".forum-thread-expand", not expanded)
        assertContentVisible(view, ".forum-thread-collapse", expanded)

    describe "tab mode", ->
        beforeEach ->
            @view = new DiscussionThreadView({ model: @thread, el: $(".thread-fixture"), mode: "tab"})

        describe "response count and pagination", ->
            renderWithContent = (view, content) ->
                DiscussionViewSpecHelper.setNextResponseContent(content)
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
                    DiscussionViewSpecHelper.setNextResponseContent({resp_total: 5, children: [{}, {}, {}, {}]})
                    @view.$el.find(".load-response-button").click()
                    assertRenderedCorrectly(@view, "5 responses", "Showing all responses", null)

                it "correctly re-render when one page remains", ->
                    DiscussionViewSpecHelper.setNextResponseContent({resp_total: 42, children: [{}, {}]})
                    @view.$el.find(".load-response-button").click()
                    assertRenderedCorrectly(@view, "42 responses", "Showing first 3 responses", "Load all responses")

                it "correctly re-render when multiple pages remain", ->
                    DiscussionViewSpecHelper.setNextResponseContent({resp_total: 111, children: [{}, {}]})
                    @view.$el.find(".load-response-button").click()
                    assertRenderedCorrectly(@view, "111 responses", "Showing first 3 responses", "Load next 100 responses")

    describe "inline mode", ->
        beforeEach ->
            @view = new DiscussionThreadView({ model: @thread, el: $(".thread-fixture"), mode: "inline"})

        describe "render", ->
            it "shows content that should be visible when collapsed", ->
                @view.render()
                assertExpandedContentVisible(@view, false)

            it "does not render any responses by default", ->
                @view.render()
                expect($.ajax).not.toHaveBeenCalled()
                expect(@view.$el.find(".responses li").length).toEqual(0)

        describe "expand/collapse", ->
            it "shows/hides appropriate content", ->
                DiscussionViewSpecHelper.setNextResponseContent({resp_total: 0, children: []})
                @view.render()
                @view.expand()
                assertExpandedContentVisible(@view, true)
                @view.collapse()
                assertExpandedContentVisible(@view, false)

            it "switches between the abbreviated and full body", ->
                DiscussionViewSpecHelper.setNextResponseContent({resp_total: 0, children: []})
                longBody = new Array(100).join("test ")
                expectedAbbreviation = DiscussionUtil.abbreviateString(longBody, 140)
                @thread.set("body", longBody)

                @view.render()
                expect($(".post-body").text()).toEqual(expectedAbbreviation)
                expect(DiscussionThreadShowView.prototype.convertMath).toHaveBeenCalled()
                DiscussionThreadShowView.prototype.convertMath.reset()

                @view.expand()
                expect($(".post-body").text()).toEqual(longBody)
                expect(DiscussionThreadShowView.prototype.convertMath).toHaveBeenCalled()
                DiscussionThreadShowView.prototype.convertMath.reset()

                @view.collapse()
                expect($(".post-body").text()).toEqual(expectedAbbreviation)
                expect(DiscussionThreadShowView.prototype.convertMath).toHaveBeenCalled()
