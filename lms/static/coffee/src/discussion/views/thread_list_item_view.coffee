class @ThreadListItemView extends Backbone.View
  tagName: "li"
  template: _.template($("#thread-list-item-template").html())
  events:
    "click a": "threadSelected"
  initialize: ->
    @model.on "change", @render
  render: =>
    @$el.html(@template(@model.toJSON()))
    @
  threadSelected: ->
    @trigger("thread:selected", @model.id)
    false
