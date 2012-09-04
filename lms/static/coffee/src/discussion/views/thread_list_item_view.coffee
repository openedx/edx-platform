class @ThreadListItemView extends Backbone.View
  tagName: "li"
  template: _.template($("#thread-list-item-template").html())

  events:
    "click a": "threadSelected"

  initialize: ->
    @model.on "change", @render
    @model.on "thread:follow", @follow
    @model.on "thread:unfollow", @unfollow

  render: =>
    @$el.html(@template(@model.toJSON()))
    if window.user.following(@model)
      @follow()
    @highlight @$(".title")
    @
  threadSelected: (event) ->
    event.preventDefault()
    @trigger("thread:selected", @model.id)

  follow: =>
    @$("a").addClass("followed")

  unfollow: =>
    @$("a").removeClass("followed")

  addComment: =>
    @$(".comments-count").html(parseInt(@$(".comments-count").html()) + 1)

  highlight: (el) ->
    el.html(el.html().replace(/&lt;mark&gt;/g, "<mark>").replace(/&lt;\/mark&gt;/g, "</mark>"))
