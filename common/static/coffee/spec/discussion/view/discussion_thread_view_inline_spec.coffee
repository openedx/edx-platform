describe "DiscussionThreadInlineView", ->
    beforeEach ->
        setFixtures(
            """
            <script type="text/template" id="_inline_thread">
                <article class="discussion-article">
                    <div class="post-body"/>
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
        spyOn(@view.showView, "convertMath")
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

        it "switches between the abbreviated and full body", ->
            DiscussionViewSpecHelper.setNextResponseContent({resp_total: 0, children: []})
            @thread.set("body", new Array(100).join("test "))
            @view.abbreviateBody()
            expect(@thread.get("body")).not.toEqual(@thread.get("abbreviatedBody"))
            @view.render()
            @view.expandPost()
            expect(@view.$el.find(".post-body").text()).toEqual(@thread.get("body"))
            expect(@view.showView.convertMath).toHaveBeenCalled()
            @view.showView.convertMath.reset()
            @view.collapsePost()
            expect(@view.$el.find(".post-body").text()).toEqual(@thread.get("abbreviatedBody"))
            expect(@view.showView.convertMath).toHaveBeenCalled()
