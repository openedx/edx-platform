describe "ThreadResponseShowView", ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        DiscussionSpecHelper.setUnderscoreFixtures()

        @user = DiscussionUtil.getUser()
        @thread = new Thread({"thread_type": "discussion"})
        @commentData = {
            id: "dummy",
            user_id: "567",
            course_id: "TestOrg/TestCourse/TestRun",
            body: "this is a comment",
            created_at: "2013-04-03T20:08:39Z",
            endorsed: false,
            abuse_flaggers: [],
            votes: {up_count: 42},
            type: "comment"
        }
        @comment = new Comment(@commentData)
        @comment.set("thread", @thread)
        @view = new ThreadResponseShowView({ model: @comment, $el: $("#fixture-element") })

        # Avoid unnecessary boilerplate
        spyOn(ThreadResponseShowView.prototype, "convertMath")

        @view.render()

    describe "voting", ->

        it "renders the vote state correctly", ->
            DiscussionViewSpecHelper.checkRenderVote(@view, @comment)

        it "votes correctly via click", ->
            DiscussionViewSpecHelper.checkUpvote(@view, @comment, @user, $.Event("click"))

        it "votes correctly via spacebar", ->
            DiscussionViewSpecHelper.checkUpvote(@view, @comment, @user, $.Event("keydown", {which: 32}))

        it "unvotes correctly via click", ->
            DiscussionViewSpecHelper.checkUnvote(@view, @comment, @user, $.Event("click"))

        it "unvotes correctly via spacebar", ->
            DiscussionViewSpecHelper.checkUnvote(@view, @comment, @user, $.Event("keydown", {which: 32}))

    it "renders endorsement correctly for a marked answer in a question thread", ->
        endorsement = {
          "username": "test_endorser",
          "time": new Date().toISOString()
        }
        @thread.set("thread_type", "question")
        @comment.set({
          "endorsed": true,
          "endorsement": endorsement
        })
        @view.render()
        expect(@view.$(".posted-details").text().replace(/\s+/g, " ")).toMatch(
          "marked as answer less than a minute ago by " + endorsement.username
        )

    it "renders anonymous endorsement correctly for a marked answer in a question thread", ->
        endorsement = {
          "username": null,
          "time": new Date().toISOString()
        }
        @thread.set("thread_type", "question")
        @comment.set({
          "endorsed": true,
          "endorsement": endorsement
        })
        @view.render()
        expect(@view.$(".posted-details").text()).toMatch("marked as answer less than a minute ago")
        expect(@view.$(".posted-details").text()).not.toMatch("\sby\s")

    it "renders endorsement correctly for an endorsed response in a discussion thread", ->
        endorsement = {
          "username": "test_endorser",
          "time": new Date().toISOString()
        }
        @thread.set("thread_type", "discussion")
        @comment.set({
          "endorsed": true,
          "endorsement": endorsement
        })
        @view.render()
        expect(@view.$(".posted-details").text().replace(/\s+/g, " ")).toMatch(
          "endorsed less than a minute ago by " + endorsement.username
        )

    it "renders anonymous endorsement correctly for an endorsed response in a discussion thread", ->
        endorsement = {
          "username": null,
          "time": new Date().toISOString()
        }
        @thread.set("thread_type", "discussion")
        @comment.set({
          "endorsed": true,
          "endorsement": endorsement
        })
        @view.render()
        expect(@view.$(".posted-details").text()).toMatch("endorsed less than a minute ago")
        expect(@view.$(".posted-details").text()).not.toMatch("\sby\s")

    it "re-renders correctly when endorsement changes", ->
        DiscussionUtil.loadRoles({"Moderator": [parseInt(window.user.id)]})
        @thread.set("thread_type", "question")
        @view.render()
        expect(@view.$(".posted-details").text()).not.toMatch("marked as answer")
        @view.$(".action-answer").click()
        expect(@view.$(".posted-details").text()).toMatch("marked as answer")
        @view.$(".action-answer").click()
        expect(@view.$(".posted-details").text()).not.toMatch("marked as answer")

    it "allows a moderator to mark an answer in a question thread", ->
        DiscussionUtil.loadRoles({"Moderator": parseInt(window.user.id)})
        @thread.set({
            "thread_type": "question",
            "user_id": (parseInt(window.user.id) + 1).toString()
        })
        @view.render()
        endorseButton = @view.$(".action-answer")
        expect(endorseButton.length).toEqual(1)
        expect(endorseButton.closest(".actions-item")).not.toHaveClass("is-hidden")
        endorseButton.click()
        expect(endorseButton).toHaveClass("is-checked")

    it "allows the author of a question thread to mark an answer", ->
        @thread.set({
            "thread_type": "question",
            "user_id": window.user.id
        })
        @view.render()
        endorseButton = @view.$(".action-answer")
        expect(endorseButton.length).toEqual(1)
        expect(endorseButton.closest(".actions-item")).not.toHaveClass("is-hidden")
        endorseButton.click()
        expect(endorseButton).toHaveClass("is-checked")

    it "does not allow the author of a discussion thread to endorse", ->
        @thread.set({
            "thread_type": "discussion",
            "user_id": window.user.id
        })
        @view.render()
        endorseButton = @view.$(".action-endorse")
        expect(endorseButton.length).toEqual(1)
        expect(endorseButton.closest(".actions-item")).toHaveClass("is-hidden")

    it "does not allow a student who is not the author of a question thread to mark an answer", ->
        @thread.set({
            "thread_type": "question",
            "user_id": (parseInt(window.user.id) + 1).toString()
        })
        @view.render()
        endorseButton = @view.$(".action-answer")
        expect(endorseButton.length).toEqual(1)
        expect(endorseButton.closest(".actions-item")).toHaveClass("is-hidden")

    describe "labels", ->

        expectOneElement = (view, selector, visible=true) =>
            view.render()
            elements = view.$el.find(selector)
            expect(elements.length).toEqual(1)
            if visible
                expect(elements).not.toHaveClass("is-hidden")
            else
                expect(elements).toHaveClass("is-hidden")

        it 'displays the reported label when appropriate for a non-staff user', ->
            expectOneElement(@view, '.post-label-reported', false)
            # flagged by current user - should be labelled
            @comment.set('abuse_flaggers', [DiscussionUtil.getUser().id])
            expectOneElement(@view, '.post-label-reported')
            # flagged by some other user but not the current one - should not be labelled
            @comment.set('abuse_flaggers', [DiscussionUtil.getUser().id + 1])
            expectOneElement(@view, '.post-label-reported', false)

        it 'displays the reported label when appropriate for a flag moderator', ->
            DiscussionSpecHelper.makeModerator()
            expectOneElement(@view, '.post-label-reported', false)
            # flagged by current user - should be labelled
            @comment.set('abuse_flaggers', [DiscussionUtil.getUser().id])
            expectOneElement(@view, '.post-label-reported')
            # flagged by some other user but not the current one - should still be labelled
            @comment.set('abuse_flaggers', [DiscussionUtil.getUser().id + 1])
            expectOneElement(@view, '.post-label-reported')

    describe "endorser display", ->

        beforeEach ->
            @comment.set('endorsement', {
                "username": "test_endorser",
                "time": new Date().toISOString()
            })
            spyOn(DiscussionUtil, 'urlFor').andReturn('test_endorser_url')

        checkUserLink = (element, is_ta, is_staff) ->
            expect(element.find('a.username').length).toEqual(1)
            expect(element.find('a.username').text()).toEqual('test_endorser')
            expect(element.find('a.username').attr('href')).toEqual('test_endorser_url')
            expect(element.find('.user-label-community-ta').length).toEqual(if is_ta then 1 else 0)
            expect(element.find('.user-label-staff').length).toEqual(if is_staff then 1 else 0)

        it "renders nothing when the response has not been endorsed", ->
            @comment.set('endorsement', null)
            expect(@view.getEndorserDisplay()).toBeNull()

        it "renders correctly for a student-endorsed response", ->
            $el = $('#fixture-element').html(@view.getEndorserDisplay())
            checkUserLink($el, false, false)

        it "renders correctly for a community TA-endorsed response", ->
            spyOn(DiscussionUtil, 'isTA').andReturn(true)
            $el = $('#fixture-element').html(@view.getEndorserDisplay())
            checkUserLink($el, true, false)

        it "renders correctly for a staff-endorsed response", ->
            spyOn(DiscussionUtil, 'isStaff').andReturn(true)
            $el = $('#fixture-element').html(@view.getEndorserDisplay())
            checkUserLink($el, false, true)
