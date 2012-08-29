class @DiscussionThreadListView extends Backbone.View
  render: ->
    @collection.each @renderThreadListItem
    @
  renderThreadListItem: (thread) =>
    view = new ThreadListItemView(model: thread)
    view.on "thread:selected", @threadSelected
    view.render()
    @$el.append(view.el)

  threadSelected: (thread_id) =>
    @trigger("thread:selected", thread_id)
