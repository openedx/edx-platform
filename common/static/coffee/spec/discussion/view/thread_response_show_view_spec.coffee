describe "ThreadResponseShowView", ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        DiscussionSpecHelper.setUnderscoreFixtures()
        appendSetFixtures('<div id="fixture-element"></div>')

        @thread = new Thread({"thread_type": "discussion"})
        @commentData = {
            id: "dummy",
            user_id: "567",
            course_id: "TestOrg/TestCourse/TestRun",
            body: "this is a comment",
            created_at: "2013-04-03T20:08:39Z",
            endorsed: false,
            abuse_flaggers: [],
            votes: {up_count: "42"}
        }
        @comment = new Comment(@commentData)
        @comment.set("thread", @thread)
        @view = new ThreadResponseShowView({ model: @comment })

        # Avoid unnecessary boilerplate
        spyOn(ThreadResponseShowView.prototype, "convertMath")

        @view.render()

    it "renders the vote correctly", ->
        DiscussionViewSpecHelper.checkRenderVote(@view, @comment)

    it "votes correctly", ->
        DiscussionViewSpecHelper.checkVote(@view, @comment, @commentData, true)

    it "unvotes correctly", ->
        DiscussionViewSpecHelper.checkUnvote(@view, @comment, @commentData, true)

    it 'toggles the vote correctly', ->
        DiscussionViewSpecHelper.checkToggleVote(@view, @comment)

    it "vote button activates on appropriate events", ->
        DiscussionViewSpecHelper.checkVoteButtonEvents(@view)

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
        expect(@view.$(".posted-details").text()).toMatch(
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
        expect(@view.$(".posted-details").text()).not.toMatch(" by ")

    it "re-renders correctly when endorsement changes", ->
        DiscussionUtil.loadRoles({"Moderator": [parseInt(window.user.id)]})
        @thread.set("thread_type", "question")
        expect(@view.$(".posted-details").text()).not.toMatch("marked as answer")
        @view.$(".action-endorse").click()
        expect(@view.$(".posted-details").text()).toMatch(
          "marked as answer less than a minute ago by " + user.get("username")
        )
        @view.$(".action-endorse").click()
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
        expect(endorseButton).not.toHaveCss({"display": "none"})
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
        expect(endorseButton).not.toHaveCss({"display": "none"})
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
        expect(endorseButton).toHaveCss({"display": "none"})
        expect(endorseButton.closest(".actions-item")).toHaveClass("is-hidden")
        endorseButton.click()
        expect(endorseButton).not.toHaveClass("is-checked")

    it "does not allow a student who is not the author of a question thread to mark an answer", ->
        @thread.set({
            "thread_type": "question",
            "user_id": (parseInt(window.user.id) + 1).toString()
        })
        @view.render()
        endorseButton = @view.$(".action-answer")
        expect(endorseButton.length).toEqual(1)
        expect(endorseButton).toHaveCss({"display": "none"})
        expect(endorseButton.closest(".actions-item")).toHaveClass("is-hidden")
        endorseButton.click()
        expect(endorseButton).not.toHaveClass("is-checked")
