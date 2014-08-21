describe "DiscussionThreadShowView", ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        DiscussionSpecHelper.setUnderscoreFixtures()

        @threadData = {
            id: "dummy",
            user_id: DiscussionUtil.getUser().id,
            username: DiscussionUtil.getUser().get('username'),
            course_id: $$course_id,
            body: "this is a thread",
            created_at: "2013-04-03T20:08:39Z",
            abuse_flaggers: [],
            votes: {up_count: "42"},
            thread_type: "discussion",
            closed: false,
            pinned: false
        }
        @thread = new Thread(@threadData)
        @view = new DiscussionThreadShowView({ model: @thread })
        @view.setElement($("#fixture-element"))
        @spyOn(@view, "convertMath")

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
                @view.render()
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
                @view.render()
                pinElem = @view.$(".discussion-pin")
                expect(pinElem.length).toEqual(1)
                expect(pinElem).toHaveClass("pinned")
                expect(pinElem).not.toHaveClass("notpinned")
                expect(pinElem.find(".pin-label")).toHaveHtml("Pinned<span class='sr'>, click to unpin</span>")
                expect(pinElem).toHaveAttr("data-tooltip", "Click to unpin")
                expect(pinElem).toHaveAttr("aria-pressed", "true")

            it "renders correctly when unpinning is not allowed", ->
                @view.render()
                pinElem = @view.$(".discussion-pin")
                expect(pinElem.length).toEqual(1)
                expect(pinElem).toHaveClass("pinned")
                expect(pinElem).not.toHaveClass("notpinned")
                expect(pinElem.find(".pin-label")).toHaveHtml("Pinned")
                expect(pinElem).not.toHaveAttr("data-tooltip")
                expect(pinElem).not.toHaveAttr("aria-pressed")
                

    it "pinning button activates on appropriate events", ->
        DiscussionViewSpecHelper.checkButtonEvents(@view, "togglePin", ".admin-pin")

    describe "labels", ->

        expectOneElement = (view, selector, visible=true) =>
            view.render()
            elements = view.$el.find(selector)
            expect(elements.length).toEqual(1)
            if visible
                expect(elements).not.toHaveClass("is-hidden")
            else
                expect(elements).toHaveClass("is-hidden")

        it 'displays the closed label when appropriate', ->
            expectOneElement(@view, '.post-label-closed', false)
            @thread.set('closed', true)
            expectOneElement(@view, '.post-label-closed')

        it 'displays the pinned label when appropriate', ->
            expectOneElement(@view, '.post-label-pinned', false)
            @thread.set('pinned', true)
            expectOneElement(@view, '.post-label-pinned')

        it 'displays the reported label when appropriate for a non-staff user', ->
            expectOneElement(@view, '.post-label-reported', false)
            # flagged by current user - should be labelled
            @thread.set('abuse_flaggers', [DiscussionUtil.getUser().id])
            expectOneElement(@view, '.post-label-reported')
            # flagged by some other user but not the current one - should not be labelled
            @thread.set('abuse_flaggers', [DiscussionUtil.getUser().id + 1])
            expectOneElement(@view, '.post-label-reported', false)

        it 'displays the reported label when appropriate for a flag moderator', ->
            DiscussionUtil.loadFlagModerator("True")
            expectOneElement(@view, '.post-label-reported', false)
            # flagged by current user - should be labelled
            @thread.set('abuse_flaggers', [DiscussionUtil.getUser().id])
            expectOneElement(@view, '.post-label-reported')
            # flagged by some other user but not the current one - should still be labelled
            @thread.set('abuse_flaggers', [DiscussionUtil.getUser().id + 1])
            expectOneElement(@view, '.post-label-reported')

    describe "author display", ->

        beforeEach ->
            @thread.set('user_url', 'test_user_url')

        checkUserLink = (element, is_ta, is_staff) ->
            expect(element.find('a.username').length).toEqual(1)
            expect(element.find('a.username').text()).toEqual('test_user')
            expect(element.find('a.username').attr('href')).toEqual('test_user_url')
            expect(element.find('.user-label-community-ta').length).toEqual(if is_ta then 1 else 0)
            expect(element.find('.user-label-staff').length).toEqual(if is_staff then 1 else 0)

        it "renders correctly for a student-authored thread", ->
            $el = $('#fixture-element').html(@view.getAuthorDisplay())
            checkUserLink($el, false, false)

        it "renders correctly for a community TA-authored thread", ->
            @thread.set('community_ta_authored', true)
            $el = $('#fixture-element').html(@view.getAuthorDisplay())
            checkUserLink($el, true, false)

        it "renders correctly for a staff-authored thread", ->
            @thread.set('staff_authored', true)
            $el = $('#fixture-element').html(@view.getAuthorDisplay())
            checkUserLink($el, false, true)

        it "renders correctly for an anonymously-authored thread", ->
            @thread.set('username', null)
            $el = $('#fixture-element').html(@view.getAuthorDisplay())
            expect($el.find('a.username').length).toEqual(0)
            expect($el.text()).toMatch(/^(\s*)anonymous(\s*)$/)
