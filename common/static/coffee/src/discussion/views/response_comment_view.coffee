if Backbone?
  class @ResponseCommentView extends DiscussionContentView
    tagName: "li"

    $: (selector) ->
      @$el.find(selector)

    initialize: ->
      super()

    render: ->
      @renderShowView()
      @

    renderSubView: (view) ->
      view.setElement(@$el)
      view.render()
      view.delegateEvents()

    renderShowView: () ->
      if not @showView?
        if @editView?
          @editView.undelegateEvents()
          @editView.$el.empty()
          @editView = null
        @showView = new ResponseCommentShowView(model: @model)
        @showView.bind "comment:_delete", @_delete
        @showView.bind "comment:edit", @edit
        @renderSubView(@showView)

    renderEditView: () ->
      if not @editView?
        if @showView?
          @showView.undelegateEvents()
          @showView.$el.empty()
          @showView = null
        @editView = new ResponseCommentEditView(model: @model)
        @editView.bind "comment:update", @update
        @editView.bind "comment:cancel_edit", @cancelEdit
        @renderSubView(@editView)

    _delete: (event) =>
      event.preventDefault()
      if not @model.can('can_delete')
        return
      if not confirm gettext("Are you sure you want to delete this comment?")
        return
      url = @model.urlFor('_delete')
      $elem = $(event.target)
      DiscussionUtil.safeAjax
        $elem: $elem
        url: url
        type: "POST"
        success: (response, textStatus) =>
          @model.remove()
          @$el.remove()
        error: =>
          DiscussionUtil.discussionAlert(
            gettext("Sorry"),
            gettext("We had some trouble deleting this comment. Please try again.")
          )

    cancelEdit: (event) =>
      @trigger "comment:cancel_edit", event
      @renderShowView()

    edit: (event) =>
      @trigger "comment:edit", event
      @renderEditView()

    update: (event) =>
      newBody = @editView.$(".edit-comment-body textarea").val()
      url = DiscussionUtil.urlFor("update_comment", @model.id)
      DiscussionUtil.safeAjax
        $elem: $(event.target)
        $loading: $(event.target)
        url: url
        type: "POST"
        dataType: "json"
        data:
          body: newBody
        error: DiscussionUtil.formErrorHandler(@$(".edit-comment-form-errors"))
        success: (response, textStatus) =>
          @model.set("body", newBody)
          @cancelEdit()
