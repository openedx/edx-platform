describe "DiscussionContentView", ->
    beforeEach ->

        setFixtures
        (
            """
            <div class="discussion-post">
                <header>
                    <a data-tooltip="vote" data-role="discussion-vote" class="vote-btn discussion-vote discussion-vote-up" href="#">
                    <span class="plus-icon">+</span> <span class="votes-count-number">0</span></a>
                    <h1>Post Title</h1>
                    <p class="posted-details">
                        <a class="username" href="/courses/MITx/999/Robot_Super_Course/discussion/forum/users/1">robot</a>
                        <span title="2013-05-08T17:34:07Z" class="timeago">less than a minute ago</span>
                    </p>
                </header>
                <div class="post-body"><p>Post body.</p></div>
                <div data-tooltip="Report Misuse" data-role="thread-flag" class="discussion-flag-abuse notflagged">
                <i class="icon"></i><span class="flag-label">Report Misuse</span></div>
                <div data-tooltip="pin this thread" data-role="thread-pin" class="admin-pin discussion-pin notpinned">
                <i class="icon"></i><span class="pin-label">Pin Thread</span></div>
            </div>
            """
        )

        @thread = new Thread {
                id: '01234567',
                user_id: '567',
                course_id: 'mitX/999/test',
                body: 'this is a thread',
                created_at: '2013-04-03T20:08:39Z',
                abuse_flaggers: ['123']
                roles: []
        }
        @view = new DiscussionContentView({ model: @thread })

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
