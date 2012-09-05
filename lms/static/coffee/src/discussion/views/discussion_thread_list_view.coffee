class @DiscussionThreadListView extends Backbone.View
  template: _.template($("#thread-list-template").html())
  events:
    "click .search": "showSearch"
    "click .browse": "toggleTopicDrop"
    "keydown .post-search-field": "performSearch"
    "click .sort-bar a": "sortThreads"
    "click .browse-topic-drop-menu": "filterTopic"
    "click .browse-topic-drop-search-input": "ignoreClick"
    "click .post-list a": "threadSelected"

  initialize: ->
    @displayedCollection = new Discussion(@collection.models)
    @collection.on "change", @reloadDisplayedCollection
    @sidebar_padding = 10
    @sidebar_header_height = 87

  reloadDisplayedCollection: (thread) =>
    thread_id = thread.get('id')
    content = @renderThread(thread)
    current_el = @$("a[data-id=#{thread_id}]")
    active = current_el.hasClass("active")
    current_el.replaceWith(content)
    if active
      @setActiveThread(thread_id)

  updateSidebar: =>

    scrollTop = $(window).scrollTop();
    windowHeight = $(window).height();

    discussionBody = $(".discussion-article")
    discussionsBodyTop = discussionBody.offset().top;
    discussionsBodyBottom = discussionsBodyTop + discussionBody.outerHeight();

    sidebar = $(".sidebar")
    if scrollTop > discussionsBodyTop - @sidebar_padding
      sidebar.addClass('fixed');
      sidebar.css('top', @sidebar_padding);
    else
      sidebar.removeClass('fixed');
      sidebar.css('top', '0');

    sidebarWidth = .31 * $(".discussion-body").width();
    sidebar.css('width', sidebarWidth + 'px');

    sidebarHeight = windowHeight - Math.max(discussionsBodyTop - scrollTop, @sidebar_padding)

    topOffset = scrollTop + windowHeight
    discussionBottomOffset = discussionsBodyBottom + @sidebar_padding
    amount = Math.max(topOffset - discussionBottomOffset, 0)

    sidebarHeight = sidebarHeight - @sidebar_padding - amount
    sidebar.css 'height', Math.min(Math.max(sidebarHeight, 400), discussionBody.outerHeight())

    postListWrapper = @$('.post-list-wrapper')
    postListWrapper.css('height', (sidebarHeight - @sidebar_header_height - 4) + 'px');


  # Because we want the behavior that when the body is clicked the menu is
  # closed, we need to ignore clicks in the search field and stop propagation.
  # Without this, clicking the search field would also close the menu.
  ignoreClick: (event) ->
      event.stopPropagation()

  render: ->
    @timer = 0
    @$el.html(@template())

    $(window).bind "scroll", @updateSidebar
    $(window).bind "resize", @updateSidebar

    @displayedCollection.on "reset", @renderThreads
    @displayedCollection.on "thread:remove", @renderThreads
    @renderThreads()
    @

  renderThreads: =>
    @$(".post-list").html("")
    rendered = $("<div></div>")
    for thread in @displayedCollection.models
      content = @renderThread(thread)
      rendered.append content
      content.wrap("<li data-id='#{thread.get('id')}' />")

    @$(".post-list").html(rendered.html())
    @trigger "threads:rendered"

  renderThread: (thread) =>
    content = $(_.template($("#thread-list-item-template").html())(thread.toJSON()))
    if thread.get('subscribed')
      content.addClass("followed")
    @highlight(content)


  highlight: (el) ->
    el.html(el.html().replace(/&lt;mark&gt;/g, "<mark>").replace(/&lt;\/mark&gt;/g, "</mark>"))

  renderThreadListItem: (thread) =>
    view = new ThreadListItemView(model: thread)
    view.on "thread:selected", @threadSelected
    view.on "thread:removed", @threadRemoved
    view.render()
    @$(".post-list").append(view.el)

  threadSelected: (e) =>
    thread_id = $(e.target).closest("a").data("id")
    @setActiveThread(thread_id)
    @trigger("thread:selected", thread_id)
    false

  threadRemoved: (thread_id) =>
    @trigger("thread:removed", thread_id)

  setActiveThread: (thread_id) ->
    @$("a[data-id!='#{thread_id}']").removeClass("active")
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
      $('body').bind 'keydown', @setActiveItem
    else
      @$(".browse-topic-drop-menu-wrapper").hide()
      $('body').unbind 'click', @toggleTopicDrop
      $('body').unbind 'keydown', @setActiveItem

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

  setActiveItem: (event) ->
    if event.which == 13
      $(".browse-topic-drop-menu-wrapper .focused").click()
      return
    if event.which != 40 && event.which != 38
      return
    event.preventDefault()

    totalItems = $(".browse-topic-drop-menu-wrapper a").length
    index = $(".browse-topic-drop-menu-wrapper .focused").parent().index()
    firstShownIndex = $($(".browse-topic-drop-menu-wrapper a").not('.hidden')[0]).parent().index()

    if event.which == 40
      index = index + 1
    else if event.which == 38
      index = index - 1
      while $(".browse-topic-drop-menu-wrapper li").eq(index).find('a').hasClass('hidden')
        index--;
    if index == totalItems
      index = 0

    while $(".browse-topic-drop-menu-wrapper li").eq(index).find('a').hasClass('hidden')
        index++;

    $(".browse-topic-drop-menu-wrapper .focused").removeClass("focused")
    $(".browse-topic-drop-menu-wrapper li").eq(index).find('a').addClass("focused")
    $(".browse-topic-drop-menu-wrapper").attr("data-focused", index)
