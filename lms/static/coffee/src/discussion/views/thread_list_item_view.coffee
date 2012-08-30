class @ThreadListItemView extends Backbone.View
  tagName: "li"
  template: _.template($("#thread-list-item-template").html())
  events:
    "click a": "threadSelected"
  initialize: ->
    @model.on "change", @render
    @model.on "thread:follow", @follow
    @model.on "thread:unfollow", @unfollow
    @model.on "comment:add", @addComment
  render: =>
    @$el.html(@template(@model.toJSON()))
    if window.user.following(@model)
      @follow()
    @
  threadSelected: ->
    @trigger("thread:selected", @model.id)
    false

  follow: =>
    @$("a").addClass("followed")

  unfollow: =>
    @$("a").removeClass("followed")

  addComment: =>
    @$(".comments-count").html(parseInt(@$(".comments-count").html()) + 1)
