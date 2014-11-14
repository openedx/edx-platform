describe "DiscussionThreadShowView", ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        DiscussionSpecHelper.setUnderscoreFixtures()

        @user = DiscussionUtil.getUser()
        @threadData = {
            id: "dummy",
            user_id: @user.id,
            username: @user.get('username'),
            course_id: $$course_id,
            title: "dummy title",
            body: "this is a thread",
            created_at: "2013-04-03T20:08:39Z",
            abuse_flaggers: [],
            votes: {up_count: 42},
            thread_type: "discussion",
            closed: false,
            pinned: false,
            type: "thread" # TODO - silly that this needs to be explicitly set
        }
        @thread = new Thread(@threadData)
        @view = new DiscussionThreadShowView({ model: @thread })
        @view.setElement($("#fixture-element"))
        @spyOn(@view, "convertMath")

    describe "voting", ->

        it "renders the vote state correctly", ->
            DiscussionViewSpecHelper.checkRenderVote(@view, @thread)

        it "votes correctly via click", ->
            DiscussionViewSpecHelper.checkUpvote(@view, @thread, @user, $.Event("click"))

        it "votes correctly via spacebar", ->
            DiscussionViewSpecHelper.checkUpvote(@view, @thread, @user, $.Event("keydown", {which: 32}))

        it "unvotes correctly via click", ->
            DiscussionViewSpecHelper.checkUnvote(@view, @thread, @user, $.Event("click"))

        it "unvotes correctly via spacebar", ->
            DiscussionViewSpecHelper.checkUnvote(@view, @thread, @user, $.Event("keydown", {which: 32}))

    describe "pinning", ->

        expectPinnedRendered = (view, model) ->
            pinned = model.get('pinned')
            button = view.$el.find(".action-pin")
            expect(button.hasClass("is-checked")).toBe(pinned)
            expect(button.attr("aria-checked")).toEqual(pinned.toString())

        it "renders the pinned state correctly", ->
            @view.render()
            expectPinnedRendered(@view, @thread)
            @thread.set('pinned', false)
            @view.render()
            expectPinnedRendered(@view, @thread)
            @thread.set('pinned', true)
            @view.render()
            expectPinnedRendered(@view, @thread)

        it "exposes the pinning control only to authorized users", ->
            @thread.updateInfo({ability: {can_openclose: false}})
            @view.render()
            expect(@view.$el.find(".action-pin").closest(".is-hidden")).toExist()
            @thread.updateInfo({ability: {can_openclose: true}})
            @view.render()
            expect(@view.$el.find(".action-pin").closest(".is-hidden")).not.toExist()

        it "handles events correctly", ->
            @view.render()
            DiscussionViewSpecHelper.checkButtonEvents(@view, "togglePin", ".action-pin")

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
            DiscussionSpecHelper.makeModerator()
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

    describe "cohorting", ->
        it "renders correctly for an uncohorted thread", ->
            @view.render()
            expect(@view.$('.group-visibility-label').text().trim()).toEqual(
                'This post is visible to everyone.'
            )

        it "renders correctly for a cohorted thread", ->
            @thread.set('group_id', '1')
            @thread.set('group_name', 'Mock Cohort')
            @view.render()
            expect(@view.$('.group-visibility-label').text().trim()).toEqual(
                'This post is visible only to Mock Cohort.'
            )
