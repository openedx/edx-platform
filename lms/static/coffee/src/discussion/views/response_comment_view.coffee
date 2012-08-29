class @ResponseCommentView extends Backbone.View
  tagName: "li"
  template: _.template($("#response-comment-template").html())
  render: ->
    @$el.html(@template(@model.toJSON()))
    @
