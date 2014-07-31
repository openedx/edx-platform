describe "ThreadResponseShowView", ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        setFixtures(
            """
            <div class="discussion-post">
                <a href="#" class="vote-btn" data-tooltip="vote" role="button" aria-pressed="false">
                    <span class="plus-icon"/><span class="votes-count-number">0</span> <span class="sr">votes (click to vote)</span>
                </a>
            </div>
            """
        )

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
        @view = new ThreadResponseShowView({ model: @comment })
        @view.setElement($(".discussion-post"))

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
