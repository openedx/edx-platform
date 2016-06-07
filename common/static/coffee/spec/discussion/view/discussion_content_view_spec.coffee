describe "DiscussionContentView", ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        DiscussionSpecHelper.setUnderscoreFixtures()

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
        @view.setElement($('#fixture-element'))
        @view.render()

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
