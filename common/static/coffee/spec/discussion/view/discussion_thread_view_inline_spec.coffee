describe "DiscussionThreadInlineView", ->
    beforeEach ->
        setFixtures(
            """
            <script type="text/template" id="_inline_thread">
                <article class="discussion-article">
                    <div class="non-cohorted-indicator"/>
                    <div class="post-extended-content">
                        <div class="response-count"/> 
                        <ol class="responses"/>
                        <div class="response-pagination"/>
                    </div>
                    <div class="post-tools">
                        <a href="javascript:void(0)" class="expand-post">Expand</a>
                        <a href="javascript:void(0)" class="collapse-post">Collapse</a>
                    </div>
                </article>
            </script>
            <script type="text/template" id="_inline_thread_cohorted">
                <article class="discussion-article">
                    <div class="cohorted-indicator"/>
                    <div class="post-extended-content">
                        <div class="response-count"/> 
                        <ol class="responses"/>
                        <div class="response-pagination"/>
                    </div>
                    <div class="post-tools">
                        <a href="javascript:void(0)" class="expand-post">Expand</a>
                        <a href="javascript:void(0)" class="collapse-post">Collapse</a>
                    </div>
                </article>
            </script>
            <div class="thread-fixture"/>
            """
        )

        @threadData = {
            id: "dummy",
            body: "dummy body",
            abuse_flaggers: [],
            votes: {up_count: "42"}
        }
        @thread = new Thread(@threadData)
        @view = new DiscussionThreadInlineView({ model: @thread })
        @view.setElement($(".thread-fixture"))
        spyOn($, "ajax")
        # Avoid unnecessary boilerplate
        spyOn(@view.showView, "render")
        spyOn(@view, "makeWmdEditor")
        spyOn(DiscussionThreadView.prototype, "renderResponse")

    assertContentVisible = (view, selector, visible) ->
        content = view.$el.find(selector)
        expect(content.length).toEqual(1)
        expect(content.is(":visible")).toEqual(visible)

    assertExpandedContentVisible = (view, expanded) ->
        expect(view.$el.hasClass("expanded")).toEqual(expanded)
        assertContentVisible(view, ".post-extended-content", expanded)
        assertContentVisible(view, ".expand-post", not expanded)
        assertContentVisible(view, ".collapse-post", expanded)

    describe "render", ->
        it "uses the cohorted template if cohorted", ->
            @view.model.set({group_id: 1})
            @view.render()
            expect(@view.$el.find(".cohorted-indicator").length).toEqual(1)

        it "uses the non-cohorted template if not cohorted", ->
            @view.render()
            expect(@view.$el.find(".non-cohorted-indicator").length).toEqual(1)

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
            @view.expandPost()
            assertExpandedContentVisible(@view, true)
            @view.collapsePost()
            assertExpandedContentVisible(@view, false)
