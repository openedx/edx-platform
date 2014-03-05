describe 'ResponseCommentView', ->
    beforeEach ->

        @comment = new Comment {
                id: '01234567',
                user_id: '567',
                course_id: 'edX/999/test',
                body: 'this is a response',
                created_at: '2013-04-03T20:08:39Z',
                abuse_flaggers: ['123']
                roles: ['Student']
        }
        @view = new ResponseCommentView({ model: @comment })
        spyOn(@view, "render")

    describe '_delete', ->
        beforeEach ->
            @comment.updateInfo {ability: {can_delete: true}}
            @event = jasmine.createSpyObj('event', ['preventDefault', 'target'])
            spyOn(@comment, "remove")
            spyOn(@view.$el, "remove")

        setAjaxResult = (isSuccess) ->
            spyOn($, "ajax").andCallFake(
                (params) =>
                    (if isSuccess then params.success else params.error) {}
                    {always: ->}
            )

        it 'requires confirmation before deleting', ->
            spyOn(window, "confirm").andReturn(false)
            setAjaxResult(true)
            @view._delete(@event)
            expect(window.confirm).toHaveBeenCalled()
            expect($.ajax).not.toHaveBeenCalled()
            expect(@comment.remove).not.toHaveBeenCalled()

        it 'removes the deleted comment object', ->
            setAjaxResult(true)
            @view._delete(@event)
            expect(@comment.remove).toHaveBeenCalled()
            expect(@view.$el.remove).toHaveBeenCalled()

        it 'calls the ajax comment deletion endpoint', ->
            setAjaxResult(true)
            @view._delete(@event)
            expect(@event.preventDefault).toHaveBeenCalled()
            expect($.ajax).toHaveBeenCalled()
            expect($.ajax.mostRecentCall.args[0].url._parts.path).toEqual('/courses/edX/999/test/discussion/comments/01234567/delete')

        it 'handles ajax errors', ->
            spyOn(DiscussionUtil, "discussionAlert")
            setAjaxResult(false)
            @view._delete(@event)
            expect(@event.preventDefault).toHaveBeenCalled()
            expect($.ajax).toHaveBeenCalled()
            expect(@comment.remove).not.toHaveBeenCalled()
            expect(@view.$el.remove).not.toHaveBeenCalled()
            expect(DiscussionUtil.discussionAlert).toHaveBeenCalled()

        it 'does not delete a comment if the permission is false', ->
            @comment.updateInfo {ability: {'can_delete': false}}
            spyOn(window, "confirm")
            setAjaxResult(true)
            @view._delete(@event)
            expect(window.confirm).not.toHaveBeenCalled()
            expect($.ajax).not.toHaveBeenCalled()
            expect(@comment.remove).not.toHaveBeenCalled()
            expect(@view.$el.remove).not.toHaveBeenCalled()

