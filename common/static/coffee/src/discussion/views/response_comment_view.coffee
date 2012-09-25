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

    renderSubView: (view) ->
      view.setElement(@$el)
      view.render()
      view.delegateEvents()

    renderShowView: () ->
      @renderSubView(@showView)
