describe "DiscussionContentView", ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        setFixtures(
            """
            <div class="discussion-post">
                <header>
                    <a href="#" class="vote-btn" data-tooltip="vote" role="button" aria-pressed="false">
                        <span class="plus-icon"/><span class='votes-count-number'>0</span> <span class="sr">votes (click to vote)</span></a>
                    <h1>Post Title</h1>
                    <p class="posted-details">
                        <a class="username" href="/courses/MITx/999/Robot_Super_Course/discussion/forum/users/1">robot</a>
                        <span title="2013-05-08T17:34:07Z" class="timeago">less than a minute ago</span>
                    </p>
                </header>
                <div class="post-body"><p>Post body.</p></div>
                <div data-tooltip="Report Misuse" data-role="thread-flag" class="discussion-flag-abuse notflagged">
                <i class="icon"></i><span class="flag-label">Report Misuse</span></div>
                <div data-tooltip="pin this thread" class="admin-pin discussion-pin notpinned">
                <i class="icon"></i><span class="pin-label">Pin Thread</span></div>
            </div>
            """
        )

        @threadData = {
            id: '01234567',
            user_id: '567',
            course_id: 'edX/999/test',
            body: 'this is a thread',
            created_at: '2013-04-03T20:08:39Z',
            abuse_flaggers: ['123'],
            votes: {up_count: '42'},
            type: "thread",
            roles: []
        }
        @thread = new Thread(@threadData)
        @view = new DiscussionContentView({ model: @thread })
        @view.setElement($('.discussion-post'))

    it 'defines the tag', ->
        expect($('#jasmine-fixtures')).toExist
        expect(@view.tagName).toBeDefined
        expect(@view.el.tagName.toLowerCase()).toBe 'div'

    it "defines the class", ->
        # spyOn @content, 'initialize'
        expect(@view.model).toBeDefined();

    it 'is tied to the model', ->
        expect(@view.model).toBeDefined();

    it 'can be flagged for abuse', ->
            @thread.flagAbuse()
            expect(@thread.get 'abuse_flaggers').toEqual ['123', '567']

    it 'can be unflagged for abuse', ->
        temp_array = []
        temp_array.push(window.user.get('id'))
        @thread.set("abuse_flaggers",temp_array)
        @thread.unflagAbuse()
        expect(@thread.get 'abuse_flaggers').toEqual []

    it 'renders the vote button properly', ->
        DiscussionViewSpecHelper.checkRenderVote(@view, @thread)

    it 'votes correctly', ->
        DiscussionViewSpecHelper.checkVote(@view, @thread, @threadData, false)

    it 'unvotes correctly', ->
        DiscussionViewSpecHelper.checkUnvote(@view, @thread, @threadData, false)

    it 'toggles the vote correctly', ->
        DiscussionViewSpecHelper.checkToggleVote(@view, @thread)
