describe "ThreadResponseShowView", ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        setFixtures(
            """
            <script type="text/template" id="thread-response-show-template">
                <a href="#" class="vote-btn" data-tooltip="vote" role="button" aria-pressed="false"></a>
                <a
                    href="javascript:void(0)"
                    class="endorse-btn action-endorse <%= thread.get('thread_type') == 'question' ? 'mark-answer' : '' %>"
                    style="cursor: default; display: none;"
                    data-tooltip="<%= thread.get('thread_type') == 'question' ? 'mark as answer' : 'endorse' %>"
                >
                    <span class="check-icon" style="pointer-events: none; "></span>
                </a>
                <p class="posted-details">
                    <span class="timeago" title="<%= created_at %>"><%= created_at %></span>
                    <% if (thread.get('thread_type') == 'question' && obj.endorsement) { %> -
                    <%=
                        interpolate(
                            endorsement.username ? "marked as answer %(time_ago)s by %(user)s" : "marked as answer %(time_ago)s",
                            {
                                'time_ago': '<span class="timeago" title="' + endorsement.time + '">' + endorsement.time + '</span>',
                                'user': endorsement.username
                            },
                            true
                        )
                    %>
                    <% } %>
                </p>
            </script>

            <div class="discussion-post"></div>
            """
        )

        @thread = new Thread({"thread_type": "discussion"})
        @commentData = {
            id: "dummy",
            user_id: "567",
            course_id: "TestOrg/TestCourse/TestRun",
            body: "this is a comment",
            created_at: "2013-04-03T20:08:39Z",
            abuse_flaggers: [],
            votes: {up_count: "42"}
        }
        @comment = new Comment(@commentData)
        @comment.set("thread", @thread)
        @view = new ThreadResponseShowView({ model: @comment })
        @view.setElement($(".discussion-post"))

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
        @thread.set("thread_type", "question")
        @comment.updateInfo({"ability": {"can_endorse": true}})
        expect(@view.$(".posted-details").text()).not.toMatch("marked as answer")
        @view.$(".action-endorse").click()
        expect(@view.$(".posted-details").text()).toMatch(
          "marked as answer less than a minute ago by " + user.get("username")
        )
        @view.$(".action-endorse").click()
        expect(@view.$(".posted-details").text()).not.toMatch("marked as answer")
