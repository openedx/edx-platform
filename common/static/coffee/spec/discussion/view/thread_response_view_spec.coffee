describe 'ThreadResponseView', ->
    beforeEach ->
        setFixtures """
            <script id="thread-response-template" type="text/template">
                <div/>
            </script>
            <div id="thread-response-fixture"/>
        """
        @response = new Comment {
            children: [{}, {}]
        }
        @view = new ThreadResponseView({model: @response, el: $("#thread-response-fixture")})
        spyOn(ThreadResponseShowView.prototype, "render")
        spyOn(ResponseCommentView.prototype, "render")

    describe 'renderComments', ->
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
