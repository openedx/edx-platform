class @ThreadListItemView extends Backbone.View
  tagName: "li"
  template: _.template($("#thread-list-item-template").html())
  events:
    "click a": "threadSelected"
  initialize: ->
    @model.on "change", @render
  render: =>
    @$el.html(@template(@model.toJSON()))
    if window.user.following(@model)
      @$("a").addClass("followed")
    @
  threadSelected: ->
    @trigger("thread:selected", @model.id)
    false
