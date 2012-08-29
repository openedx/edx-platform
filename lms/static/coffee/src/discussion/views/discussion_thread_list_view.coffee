class @DiscussionThreadListView extends Backbone.View
  render: ->
    @collection.each @renderThreadListItem
    @
  renderThreadListItem: (thread) =>
    view = new ThreadListItemView(model: thread)
    view.render()
    @$el.append(view.el)
