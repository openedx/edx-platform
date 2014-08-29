describe 'ThreadResponseView', ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        DiscussionSpecHelper.setUnderscoreFixtures()

        @response = new Comment {
            children: [{}, {}]
        }
        @view = new ThreadResponseView({model: @response, el: $("#fixture-element")})
        spyOn(ThreadResponseShowView.prototype, "render")
        spyOn(ResponseCommentView.prototype, "render")

    describe 'renderComments', ->
        it 'hides "show comments" link if collapseComments is not set', ->
            @view.render()
            expect(@view.$(".comments")).toBeVisible()
            expect(@view.$(".action-show-comments")).not.toBeVisible()

        it 'hides "show comments" link if collapseComments is set but response has no comments', ->
            @response = new Comment { children: [] }
            @view = new ThreadResponseView({
                model: @response, el: $("#fixture-element"),
                collapseComments: true
            })
            @view.render()
            expect(@view.$(".comments")).toBeVisible()
            expect(@view.$(".action-show-comments")).not.toBeVisible()

        it 'hides comments if collapseComments is set and shows them when "show comments" link is clicked', ->
            @view = new ThreadResponseView({
                model: @response, el: $("#fixture-element"),
                collapseComments: true
            })
            @view.render()
            expect(@view.$(".comments")).not.toBeVisible()
            expect(@view.$(".action-show-comments")).toBeVisible()
            @view.$(".action-show-comments").click()
            expect(@view.$(".comments")).toBeVisible()
            expect(@view.$(".action-show-comments")).not.toBeVisible()

        it 'populates commentViews and binds events', ->
            # Ensure that edit view is set to test invocation of cancelEdit
            @view.createEditView()
            spyOn(@view, 'cancelEdit')
            spyOn(@view, 'cancelCommentEdits')
            spyOn(@view, 'hideCommentForm')
            spyOn(@view, 'showCommentForm')
            @view.renderComments()
            expect(@view.commentViews.length).toEqual(2)
            @view.commentViews[0].trigger "comment:edit", jasmine.createSpyObj("event", ["preventDefault"])
            expect(@view.cancelEdit).toHaveBeenCalled()
            expect(@view.cancelCommentEdits).toHaveBeenCalled()
            expect(@view.hideCommentForm).toHaveBeenCalled()
            @view.commentViews[0].trigger "comment:cancel_edit"
            expect(@view.showCommentForm).toHaveBeenCalled()

    describe 'cancelCommentEdits', ->
        it 'calls cancelEdit on each comment view', ->
            @view.renderComments()
            expect(@view.commentViews.length).toEqual(2)
            _.each(@view.commentViews, (commentView) -> spyOn(commentView, 'cancelEdit'))
            @view.cancelCommentEdits()
            _.each(@view.commentViews, (commentView) -> expect(commentView.cancelEdit).toHaveBeenCalled())
