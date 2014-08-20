describe 'ResponseCommentShowView', ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        # set up the container for the response to go in
        DiscussionSpecHelper.setUnderscoreFixtures()
        appendSetFixtures('<ol class="responses"></ol>')

        # set up a model for a new Comment
        @comment = new Comment {
                id: '01234567',
                user_id: '567',
                course_id: 'edX/999/test',
                body: 'this is a response',
                created_at: '2013-04-03T20:08:39Z',
                abuse_flaggers: ['123']
                roles: []
        }
        @view = new ResponseCommentShowView({ model: @comment })
        spyOn(@view, "convertMath")

    it 'defines the tag', ->
        expect($('#jasmine-fixtures')).toExist
        expect(@view.tagName).toBeDefined
        expect(@view.el.tagName.toLowerCase()).toBe 'li'

    it 'is tied to the model', ->
        expect(@view.model).toBeDefined()

    describe 'rendering', ->

        beforeEach ->
            spyOn(@view, 'renderAttrs')

        it 'produces the correct HTML', ->
            @view.render()
            expect(@view.el.innerHTML).toContain('"discussion-flag-abuse notflagged"')

        it 'can be flagged for abuse', ->
            @comment.flagAbuse()
            expect(@comment.get 'abuse_flaggers').toEqual ['123', '567']

        it 'can be unflagged for abuse', ->
            temp_array = []
            temp_array.push(window.user.get('id'))
            @comment.set("abuse_flaggers",temp_array)
            @comment.unflagAbuse()
            expect(@comment.get 'abuse_flaggers').toEqual []

    describe '_delete', ->

        it 'triggers on the correct events', ->
            DiscussionUtil.loadRoles []
            @comment.updateInfo {ability: {'can_delete': true}}
            @view.render()
            DiscussionViewSpecHelper.checkButtonEvents(@view, "_delete", ".action-delete")

        it 'triggers the delete event', ->
            triggerTarget = jasmine.createSpy()
            @view.bind "comment:_delete", triggerTarget
            @view._delete()
            expect(triggerTarget).toHaveBeenCalled()

    describe 'edit', ->

        it 'triggers on the correct events', ->
            DiscussionUtil.loadRoles []
            @comment.updateInfo {ability: {'can_edit': true}}
            @view.render()
            DiscussionViewSpecHelper.checkButtonEvents(@view, "edit", ".action-edit")

        it 'triggers comment:edit when the edit button is clicked', ->
            triggerTarget = jasmine.createSpy()
            @view.bind "comment:edit", triggerTarget
            @view.edit()
            expect(triggerTarget).toHaveBeenCalled()
