xdescribe "DiscussionContentView", ->
    beforeEach ->

        setFixtures
        '''
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
        '''
        @

    it "defines the class", ->
        # spyOn @content, 'initialize'
        myView = new DiscussionContentView(new Content)
        expect(myView.tagName).toBeDefined()
