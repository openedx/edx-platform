describe 'ResponseCommentView', ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        @comment = new Comment {
                id: '01234567',
                user_id: user.id,
                course_id: $$course_id,
                body: 'this is a response',
                created_at: '2013-04-03T20:08:39Z',
                abuse_flaggers: ['123']
                roles: ['Student']
        }
        DiscussionSpecHelper.setUnderscoreFixtures()

        @view = new ResponseCommentView({ model: @comment, el: $("#fixture-element") })
        spyOn(ResponseCommentShowView.prototype, "convertMath")
        spyOn(DiscussionUtil, "makeWmdEditor")
        @view.render()

    makeEventSpy = () -> jasmine.createSpyObj('event', ['preventDefault', 'target'])

    describe '_delete', ->
        beforeEach ->
            @comment.updateInfo {ability: {can_delete: true}}
            @event = makeEventSpy()
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

    describe 'renderShowView', ->
        it 'renders the show view, removes the edit view, and registers event handlers', ->
            spyOn(@view, "_delete")
            spyOn(@view, "edit")
            # Without calling renderEditView first, renderShowView is a no-op
            @view.renderEditView()
            @view.renderShowView()
            @view.showView.trigger "comment:_delete", makeEventSpy()
            expect(@view._delete).toHaveBeenCalled()
            @view.showView.trigger "comment:edit", makeEventSpy()
            expect(@view.edit).toHaveBeenCalled()
            expect(@view.$(".edit-post-form#comment_#{@comment.id}")).not.toHaveClass("edit-post-form")

    describe 'renderEditView', ->
        it 'renders the edit view, removes the show view, and registers event handlers', ->
            spyOn(@view, "update")
            spyOn(@view, "cancelEdit")
            @view.renderEditView()
            @view.editView.trigger "comment:update", makeEventSpy()
            expect(@view.update).toHaveBeenCalled()
            @view.editView.trigger "comment:cancel_edit", makeEventSpy()
            expect(@view.cancelEdit).toHaveBeenCalled()
            expect(@view.$(".edit-post-form#comment_#{@comment.id}")).toHaveClass("edit-post-form")

    describe 'edit', ->
        it 'triggers the appropriate event and switches to the edit view', ->
            spyOn(@view, 'renderEditView')
            editTarget = jasmine.createSpy()
            @view.bind "comment:edit", editTarget
            @view.edit()
            expect(@view.renderEditView).toHaveBeenCalled()
            expect(editTarget).toHaveBeenCalled()

    describe 'with edit view displayed', ->
        beforeEach ->
            @view.renderEditView()

        describe 'cancelEdit', ->
            it 'triggers the appropriate event and switches to the show view', ->
                spyOn(@view, 'renderShowView')
                cancelEditTarget = jasmine.createSpy()
                @view.bind "comment:cancel_edit", cancelEditTarget
                @view.cancelEdit()
                expect(@view.renderShowView).toHaveBeenCalled()
                expect(cancelEditTarget).toHaveBeenCalled()

        describe 'update', ->
            beforeEach ->
                @updatedBody = "updated body"
                # Markdown code creates the editor, so we simulate that here
                @view.$el.find(".edit-comment-body").html($("<textarea></textarea>"))
                @view.$el.find(".edit-comment-body textarea").val(@updatedBody)
                spyOn(@view, 'cancelEdit')
                spyOn($, "ajax").andCallFake(
                    (params) =>
                        if @ajaxSucceed
                            params.success()
                        else
                            params.error({status: 500})
                        {always: ->}
                )

            it 'calls the update endpoint correctly and displays the show view on success', ->
                @ajaxSucceed = true
                @view.update(makeEventSpy())
                expect($.ajax).toHaveBeenCalled()
                expect($.ajax.mostRecentCall.args[0].url._parts.path).toEqual('/courses/edX/999/test/discussion/comments/01234567/update')
                expect($.ajax.mostRecentCall.args[0].data.body).toEqual(@updatedBody)
                expect(@view.model.get("body")).toEqual(@updatedBody)
                expect(@view.cancelEdit).toHaveBeenCalled()

            it 'handles AJAX errors', ->
                originalBody = @comment.get("body")
                @ajaxSucceed = false
                @view.update(makeEventSpy())
                expect($.ajax).toHaveBeenCalled()
                expect($.ajax.mostRecentCall.args[0].url._parts.path).toEqual('/courses/edX/999/test/discussion/comments/01234567/update')
                expect($.ajax.mostRecentCall.args[0].data.body).toEqual(@updatedBody)
                expect(@view.model.get("body")).toEqual(originalBody)
                expect(@view.cancelEdit).not.toHaveBeenCalled()
                expect(@view.$(".edit-comment-form-errors *").length).toEqual(1)
