describe "DiscussionThreadShowView", ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        setFixtures(
            """
            <div class="discussion-post">
                <a href="#" class="vote-btn" data-tooltip="vote" role="button" aria-pressed="false">
                    <span class="plus-icon"/><span class="votes-count-number">0</span> <span class="sr">votes (click to vote)</span>
                </a>
                <div class="admin-pin discussion-pin notpinned" role="button" aria-pressed="false" tabindex="0">
                    <i class="icon icon-pushpin"></i>
                    <span class="pin-label">Pin Thread</span>
                </div>
            </div>
            """
        )

        @threadData = {
            id: "dummy",
            user_id: user.id,
            course_id: $$course_id,
            body: "this is a thread",
            created_at: "2013-04-03T20:08:39Z",
            abuse_flaggers: [],
            votes: {up_count: "42"}
        }
        @thread = new Thread(@threadData)
        @view = new DiscussionThreadShowView({ model: @thread })
        @view.setElement($(".discussion-post"))

    it "renders the vote correctly", ->
        DiscussionViewSpecHelper.checkRenderVote(@view, @thread)

    it "votes correctly", ->
        DiscussionViewSpecHelper.checkVote(@view, @thread, @threadData, true)

    it "unvotes correctly", ->
        DiscussionViewSpecHelper.checkUnvote(@view, @thread, @threadData, true)

    it 'toggles the vote correctly', ->
        DiscussionViewSpecHelper.checkToggleVote(@view, @thread)

    it "vote button activates on appropriate events", ->
        DiscussionViewSpecHelper.checkVoteButtonEvents(@view)

    describe "renderPinned", ->
        describe "for an unpinned thread", ->
            it "renders correctly when pinning is allowed", ->
                @thread.updateInfo({ability: {can_openclose: true}})
                @view.renderPinned()
                pinElem = @view.$(".discussion-pin")
                expect(pinElem.length).toEqual(1)
                expect(pinElem).not.toHaveClass("pinned")
                expect(pinElem).toHaveClass("notpinned")
                expect(pinElem.find(".pin-label")).toHaveHtml("Pin Thread")
                expect(pinElem).not.toHaveAttr("data-tooltip")
                expect(pinElem).toHaveAttr("aria-pressed", "false")

            # If pinning is not allowed, the pinning UI is not present, so no
            # test is needed

        describe "for a pinned thread", ->
            beforeEach ->
                @thread.set("pinned", true)

            it "renders correctly when unpinning is allowed", ->
                @thread.updateInfo({ability: {can_openclose: true}})
                @view.renderPinned()
                pinElem = @view.$(".discussion-pin")
                expect(pinElem.length).toEqual(1)
                expect(pinElem).toHaveClass("pinned")
                expect(pinElem).not.toHaveClass("notpinned")
                expect(pinElem.find(".pin-label")).toHaveHtml("Pinned<span class='sr'>, click to unpin</span>")
                expect(pinElem).toHaveAttr("data-tooltip", "Click to unpin")
                expect(pinElem).toHaveAttr("aria-pressed", "true")

            it "renders correctly when unpinning is not allowed", ->
                @view.renderPinned()
                pinElem = @view.$(".discussion-pin")
                expect(pinElem.length).toEqual(1)
                expect(pinElem).toHaveClass("pinned")
                expect(pinElem).not.toHaveClass("notpinned")
                expect(pinElem.find(".pin-label")).toHaveHtml("Pinned")
                expect(pinElem).not.toHaveAttr("data-tooltip")
                expect(pinElem).not.toHaveAttr("aria-pressed")
                

    it "pinning button activates on appropriate events", ->
        DiscussionViewSpecHelper.checkButtonEvents(@view, "togglePin", ".admin-pin")
