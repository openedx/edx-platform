class @ThreadResponseView extends Backbone.View
  tagName: "li"
  template: _.template($("#thread-response-template").html())
  render: ->
    @$el.html(@template(@model.toJSON()))
    @renderComments()
    @

  renderComments: ->
      @model.get("comments").each @renderComment

  renderComment: (comment) =>
    view = new ResponseCommentView(model: comment)
    view.render()
    @$(".comments").append(view.el)
