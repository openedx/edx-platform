class @DiscussionThreadListView extends Backbone.View
  template: _.template($("#thread-list-template").html())
  events:
    "click .search": "showSearch"
    "click .browse": "toggleTopicDrop"
    "keydown .post-search-field": "performSearch"
    "click .sort-bar a": "sortThreads"
    "click .browse-topic-drop-menu": "filterTopic"
    "click .browse-topic-drop-search-input": "ignoreClick"

  initialize: ->
    @displayedCollection = new Discussion(@collection.models)
    @collection.on "change", @reloadDisplayedCollection

  reloadDisplayedCollection: =>
    @displayedCollection.reset(@collection.models)


  # Because we want the behavior that when the body is clicked the menu is
  # closed, we need to ignore clicks in the search field and stop propagation.
  # Without this, clicking the search field would also close the menu.
  ignoreClick: (event) ->
      event.stopPropagation()

  render: ->
    @timer = 0
    @$el.html(@template())
    @displayedCollection.on "reset", @renderThreads
    @renderThreads()
    @

  renderThreads: =>
    @$(".post-list").html("")
    @displayedCollection.each @renderThreadListItem
    @trigger "threads:rendered"

  renderThreadListItem: (thread) =>
    view = new ThreadListItemView(model: thread)
    view.on "thread:selected", @threadSelected
    view.render()
    @$(".post-list").append(view.el)

  threadSelected: (thread_id) =>
    @setActiveThread(thread_id)
    @trigger("thread:selected", thread_id)

  setActiveThread: (thread_id) ->
    @$(".post-list a").removeClass("active")
    @$("a[data-id='#{thread_id}']").addClass("active")

  showSearch: ->
    @$(".search").addClass('is-open')
    @$(".browse").removeClass('is-open')
    setTimeout (-> @$(".post-search-field").focus()), 200

  toggleTopicDrop: (event) =>
    event.stopPropagation()
    @$(".browse").toggleClass('is-dropped')
    if @$(".browse").hasClass('is-dropped')
      @$(".browse-topic-drop-menu-wrapper").show()
      $('body').bind 'click', @toggleTopicDrop
    else
      @$(".browse-topic-drop-menu-wrapper").hide()
      $('body').unbind 'click', @toggleTopicDrop

  setTopic: (event) ->
    item = $(event.target).closest('a')
    boardName = item.find(".board-name").html()
    _.each item.parents('ul').not('.browse-topic-drop-menu'), (parent) ->
      boardName = $(parent).siblings('a').find('.board-name').html() + ' / ' + boardName
    @$(".current-board").html(boardName)
    fontSize = 16
    @$(".current-board").css('font-size', '16px')

    while @$(".current-board").width() > (@$el.width() * .8) - 40
      fontSize--
      if fontSize < 11
        break
      @$(".current-board").css('font-size', fontSize + 'px')

  filterTopic: (event) ->
    @setTopic(event)
    item = $(event.target).closest('li')
    if item.find("span.board-name").data("discussion_id") == "#all"
      item = item.parent()
    discussionIds = _.compact _.map item.find("span.board-name"), (board) -> $(board).data("discussion_id")
    discussionIds = _.map discussionIds, (info) -> info.id
    filtered = @collection.filter (thread) =>
      _.include(discussionIds, thread.get('commentable_id'))
    @displayedCollection.reset filtered

  sortThreads: (event) ->
    @$(".sort-bar a").removeClass("active")
    $(event.target).addClass("active")
    sortBy = $(event.target).data("sort")
    if sortBy == "date"
      @displayedCollection.comparator = @displayedCollection.sortByDateRecentFirst
    else if sortBy == "votes"
      @displayedCollection.comparator = @displayedCollection.sortByVotes
    else if sortBy == "comments"
      @displayedCollection.comparator = @displayedCollection.sortByComments
    @displayedCollection.sort()

  performSearch: (event) ->
    if event.which == 13
      event.preventDefault()
      url = DiscussionUtil.urlFor("search")
      text = @$(".post-search-field").val()
      DiscussionUtil.safeAjax
        $elem: @$(".post-search-field")
        data: { text: text }
        url: url
        type: "GET"
        success: (response, textStatus) =>
          if textStatus == 'success'
            @collection.reset(response.discussion_data)
            @displayedCollection.reset(@collection.models)
