describe 'ResponseCommentShowView', ->
    beforeEach ->
        # set up the container for the response to go in
        setFixtures """
        <ol class="responses"></ol>
        <script id="response-comment-show-template" type="text/template">
            <div id="comment_<%- id %>">
            <div class="response-body"><%- body %></div>
            <div class="discussion-flag-abuse notflagged" data-role="thread-flag" data-tooltip="report misuse">
            <i class="icon"></i><span class="flag-label"></span></div>
            <p class="posted-details">&ndash;posted <span class="timeago" title="<%- created_at %>"><%- created_at %></span> by
            <% if (obj.username) { %>
            <a href="<%- user_url %>" class="profile-link"><%- username %></a>
            <% } else {print('anonymous');} %>
            </p>
            </div>
        </script>
        """

        # set up a model for a new Comment
        @response = new Comment {
                id: '01234567',
                user_id: '567',
                course_id: 'mitX/999/test',
                body: 'this is a response',
                created_at: '2013-04-03T20:08:39Z',
                abuse_flaggers: ['123']
                roles: []
        }
        @view = new ResponseCommentShowView({ model: @response })

        # spyOn(DiscussionUtil, 'loadRoles').andReturn []

    it 'defines the tag', ->
        expect($('#jasmine-fixtures')).toExist
        expect(@view.tagName).toBeDefined
        expect(@view.el.tagName.toLowerCase()).toBe 'li'

    it 'is tied to the model', ->
        expect(@view.model).toBeDefined();

    describe 'rendering', ->

        beforeEach ->
            spyOn(@view, 'renderAttrs')
            spyOn(@view, 'markAsStaff')
            spyOn(@view, 'convertMath')

        it 'produces the correct HTML', ->
            @view.render()
            expect(@view.el.innerHTML).toContain('"discussion-flag-abuse notflagged"')

        it 'can be flagged for abuse', ->
            @response.flagAbuse()
            expect(@response.get 'abuse_flaggers').toEqual ['123', '567']

        it 'can be unflagged for abuse', ->
            temp_array = []
            temp_array.push(window.user.get('id'))
            @response.set("abuse_flaggers",temp_array)
            @response.unflagAbuse()
            expect(@response.get 'abuse_flaggers').toEqual []
