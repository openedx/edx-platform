if Backbone?
  class @ResponseCommentView extends DiscussionContentView
    tagName: "li"

    $: (selector) ->
      @$el.find(selector)

    initialize: ->
      super()
      @createShowView()

    render: ->
      @renderShowView()
      @

    createShowView: () ->

      if @editView?
        @editView.undelegateEvents()
        @editView.$el.empty()
        @editView = null

      @showView = new ResponseCommentShowView(model: @model)
      @showView.bind "comment:_delete", @_delete

    renderSubView: (view) ->
      view.setElement(@$el)
      view.render()
      view.delegateEvents()

    renderShowView: () ->
      @renderSubView(@showView)

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
