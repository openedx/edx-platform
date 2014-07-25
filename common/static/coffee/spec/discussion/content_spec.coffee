describe 'All Content', ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()

    describe 'Staff and TA Content', ->
        beforeEach ->
            DiscussionUtil.loadRoles({"Moderator": [567], "Administrator": [567], "Community TA": [567]})

        it 'anonymous thread should not include login role label', ->
            anon_content = new Content
            anon_content.initialize
            expect(anon_content.get 'staff_authored').toBe false
            expect(anon_content.get 'community_ta_authored').toBe false

        it 'general thread should include login role label', ->
            anon_content = new Content { user_id: '567' }
            anon_content.initialize
            expect(anon_content.get 'staff_authored').toBe true
            expect(anon_content.get 'community_ta_authored').toBe true

    describe 'Content', ->
        beforeEach ->
            @content = new Content {
                id: '01234567',
                user_id: '567',
                course_id: 'edX/999/test',
                body: 'this is some content',
                abuse_flaggers: ['123']
            }

        it 'should exist', ->
            expect(Content).toBeDefined()

        it 'is initialized correctly', ->
            @content.initialize
            expect(Content.contents['01234567']).toEqual @content
            expect(@content.get 'id').toEqual '01234567'
            expect(@content.get 'user_url').toEqual '/courses/edX/999/test/discussion/forum/users/567'
            expect(@content.get 'children').toEqual []
            expect(@content.get 'comments').toEqual(jasmine.any(Comments))

        it 'can update info', ->
            @content.updateInfo {
                                ability: 'can_endorse',
                                voted: true,
                                subscribed: true
                                }
            expect(@content.get 'ability').toEqual 'can_endorse'
            expect(@content.get 'voted').toEqual true
            expect(@content.get 'subscribed').toEqual true

        it 'can be flagged for abuse', ->
            @content.flagAbuse()
            expect(@content.get 'abuse_flaggers').toEqual ['123', '567']

        it 'can be unflagged for abuse', ->
            temp_array = []
            temp_array.push(window.user.get('id'))
            @content.set("abuse_flaggers",temp_array)
            @content.unflagAbuse()
            expect(@content.get 'abuse_flaggers').toEqual []

    describe 'Comments', ->
        beforeEach ->
            @comment1 = new Comment {id: '123'}
            @comment2 = new Comment {id: '345'}

        it 'can contain multiple comments', ->
            myComments = new Comments
            expect(myComments.length).toEqual 0
            myComments.add @comment1
            expect(myComments.length).toEqual 1
            myComments.add @comment2
            expect(myComments.length).toEqual 2

        it 'returns results to the find method', ->
            myComments = new Comments
            myComments.add @comment1
            expect(myComments.find('123')).toBe @comment1
