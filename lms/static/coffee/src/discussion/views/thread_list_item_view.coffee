class @ThreadListItemView extends Backbone.View
  tagName: "li"
  template: _.template($("#thread-list-item-template").html())
  initialize: ->
    @model.on "change", @render
  render: =>
    @$el.html(@template(@model.toJSON()))
    @
