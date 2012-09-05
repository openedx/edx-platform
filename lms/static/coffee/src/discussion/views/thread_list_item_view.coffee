class @ThreadListItemView extends Backbone.View
  tagName: "li"
  template: _.template($("#thread-list-item-template").html())
  events:
    "click a": "threadSelected"
  initialize: ->
    @model.on "change", @render
    @model.on "thread:remove", @threadRemoved
    @model.on "thread:follow", @follow
    @model.on "thread:unfollow", @unfollow
    @model.on "comment:add", @addComment
    @model.on "comment:remove", @removeComment
  render: =>
    @$el.html(@template(@model.toJSON()))
    if window.user.following(@model)
      @follow()
    @

  threadSelected: (event) ->
    event.preventDefault()
    @trigger("thread:selected", @model.id)

  threadRemoved: =>
    @trigger("thread:removed", @model.id)

  follow: =>
    @$("a").addClass("followed")

  unfollow: =>
    @$("a").removeClass("followed")

  addComment: (comment) =>
    @$(".comments-count").html(@model.get('comments_count'))

  removeComment: (comment) =>
    @$(".comments-count").html(@model.get('comments_count'))
