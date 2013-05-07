describe "ResponseCommentShowView", ->
    beforeEach ->
        setFixtures """
        <li>
            <div id="comment_518910eab02379ff16000001">
                <div class="response-body"><p>This is a comment</p></div>
                <div data-tooltip="report misuse" data-role="thread-flag" class="discussion-flag-abuse notflagged">
                    <i class="icon"></i>
                    <span class="flag-label"></span>
                </div>
                    <p class="posted-details">&ndash;posted
                        <span title="2013-05-07T14:34:18Z" class="timeago">about a minute ago</span> by
                        <a class="profile-link" href="/courses/MITx/999/Robot_Super_Course/discussion/forum/users/3">student</a>
                    </p>
            </div>
        </li>
        """
        # spyOn($.fn, 'load').andReturn(@moduleData)

        @showView = new ResponseCommentShowView(
          el: $("li")
        )

    describe "class definition", ->
        it "sets the correct tagName", ->
            expect(@showView.tagName).toEqual("li")
