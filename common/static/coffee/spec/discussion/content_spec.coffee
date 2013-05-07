describe 'Content', ->
    beforeEach ->
        # TODO: figure out a better way of handling this
        # It is set up in main.coffee DiscussionApp.start
        window.$$course_id = 'mitX/999/test'
        window.user = new DiscussionUser {id: '567'}

        @content = new Content {
            id: '01234567',
            user_id: '567',
            course_id: 'mitX/999/test',
            body: 'this is some content',
            abuse_flaggers: ['123']
        }

    it 'should exist', ->
        expect(Content).toBeDefined()

    it 'is initialized correctly', ->
        @content.initialize
        expect(Content.contents['01234567']).toEqual @content
        expect(@content.get 'id').toEqual '01234567'
        expect(@content.get 'user_url').toEqual '/courses/mitX/999/test/discussion/forum/users/567'
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

    describe 'can be flagged and unflagged', ->
        beforeEach ->
            spyOn @content, 'trigger'

        it 'can be flagged for abuse', ->
            @content.flagAbuse
            expect(@content.get 'abuse_flaggers').toEqual ['123', '567']
