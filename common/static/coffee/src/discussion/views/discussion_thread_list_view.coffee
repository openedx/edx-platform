if Backbone?
  class @DiscussionThreadListView extends Backbone.View
    events:
      "click .search": "showSearch"
      "click .home": "goHome"
      "click .browse": "toggleTopicDrop"
      "keydown .post-search-field": "performSearch"
      "focus .post-search-field": "showSearch"
      "change .forum-nav-sort-control": "sortThreads"
      "click .browse-topic-drop-menu": "filterTopic"
      "click .browse-topic-drop-search-input": "ignoreClick"
      "click .forum-nav-thread-link": "threadSelected"
      "click .forum-nav-load-more-link": "loadMorePages"
      "change .forum-nav-filter-cohort-control": "chooseCohort"
      'keyup .browse-topic-drop-search-input': DiscussionFilter.filterDrop

    initialize: ->
      @displayedCollection = new Discussion(@collection.models, pages: @collection.pages)
      @collection.on "change", @reloadDisplayedCollection
      @discussionIds=""
      @collection.on "reset", (discussion) =>
        board = $(".current-board").html()
        @displayedCollection.current_page = discussion.current_page
        @displayedCollection.pages = discussion.pages
        @displayedCollection.reset discussion.models
        # TODO: filter correctly
        # target = _.filter($("a.topic:contains('#{board}')"), (el) -> el.innerText == "General" || el.innerHTML == "General")
        # if target.length > 0
        #   @filterTopic($.Event("filter", {'target': target[0]}))
      @collection.on "add", @addAndSelectThread
      @sidebar_padding = 10
      @boardName
      @template = _.template($("#thread-list-template").html())
      @current_search = ""
      @mode = 'all'

      @searchAlertCollection = new Backbone.Collection([], {model: Backbone.Model})

      @searchAlertCollection.on "add", (searchAlert) =>
        content = _.template(
          $("#search-alert-template").html(),
          {'message': searchAlert.attributes.message, 'cid': searchAlert.cid}
          )
        @$(".search-alerts").append(content)
        @$("#search-alert-" + searchAlert.cid + " a.dismiss").bind "click", searchAlert, (event) =>
          @removeSearchAlert(event.data.cid)

      @searchAlertCollection.on "remove", (searchAlert) =>
        @$("#search-alert-" + searchAlert.cid).remove()

      @searchAlertCollection.on "reset", =>
        @$(".search-alerts").empty()

    addSearchAlert: (message) =>
      m = new Backbone.Model({"message": message})
      @searchAlertCollection.add(m)
      m

    removeSearchAlert: (searchAlert) =>
      @searchAlertCollection.remove(searchAlert)

    clearSearchAlerts: =>
      @searchAlertCollection.reset()

    reloadDisplayedCollection: (thread) =>
      @clearSearchAlerts()
      thread_id = thread.get('id')
      content = @renderThread(thread)
      current_el = @$(".forum-nav-thread[data-id=#{thread_id}]")
      active = current_el.has(".forum-nav-thread-link.is-active").length != 0
      current_el.replaceWith(content)
      @showMetadataAccordingToSort()
      if active
        @setActiveThread(thread_id)


    #TODO fix this entire chain of events
    addAndSelectThread: (thread) =>
      commentable_id = thread.get("commentable_id")
      commentable = @$(".board-name[data-discussion_id]").filter(-> $(this).data("discussion_id").id == commentable_id)
      @setTopicHack(commentable)
      @retrieveDiscussion commentable_id, =>
        @trigger "thread:created", thread.get('id')

    updateSidebar: =>

      scrollTop = $(window).scrollTop();
      windowHeight = $(window).height();

      discussionBody = $(".discussion-column")
      discussionsBodyTop = if discussionBody[0] then discussionBody.offset().top
      discussionsBodyBottom = discussionsBodyTop + discussionBody.outerHeight()

      sidebar = $(".sidebar")
      if scrollTop > discussionsBodyTop - @sidebar_padding
        sidebar.css('top', scrollTop - discussionsBodyTop + @sidebar_padding);
      else
        sidebar.css('top', '0');

      sidebarWidth = .31 * $(".discussion-body").width();
      sidebar.css('width', sidebarWidth + 'px');

      sidebarHeight = windowHeight - Math.max(discussionsBodyTop - scrollTop, @sidebar_padding)

      topOffset = scrollTop + windowHeight
      discussionBottomOffset = discussionsBodyBottom + @sidebar_padding
      amount = Math.max(topOffset - discussionBottomOffset, 0)

      sidebarHeight = sidebarHeight - @sidebar_padding - amount
      sidebarHeight = Math.min(sidebarHeight + 1, discussionBody.outerHeight())
      sidebar.css 'height', sidebarHeight

      browseSearchHeight = @$(".browse-search").outerHeight()
      refineBarHeight = @$(".forum-nav-refine-bar").outerHeight()
      @$('.forum-nav-thread-list').css('height', (sidebarHeight - browseSearchHeight - refineBarHeight - 2) + 'px')


    # Because we want the behavior that when the body is clicked the menu is
    # closed, we need to ignore clicks in the search field and stop propagation.
    # Without this, clicking the search field would also close the menu.
    ignoreClick: (event) ->
        event.stopPropagation()

    render: ->
      @timer = 0
      @$el.html(@template())
      @$(".forum-nav-sort-control").val(@collection.sort_preference)

      $(window).bind "load", @updateSidebar
      $(window).bind "scroll", @updateSidebar
      $(window).bind "resize", @updateSidebar

      @displayedCollection.on "reset", @renderThreads
      @displayedCollection.on "thread:remove", @renderThreads
      @renderThreads()
      @

    renderThreads: =>
      @$(".forum-nav-thread-list").html("")
      rendered = $("<div></div>")
      for thread in @displayedCollection.models
        content = @renderThread(thread)
        rendered.append content

      @$(".forum-nav-thread-list").html(rendered.html())
      @showMetadataAccordingToSort()

      @renderMorePages()
      @updateSidebar()
      @trigger "threads:rendered"

    showMetadataAccordingToSort: () =>
      # Ensure that threads display metadata appropriate for the current sort
      voteCounts = @$(".forum-nav-thread-votes-count")
      commentCounts = @$(".forum-nav-thread-comments-count")
      voteCounts.hide()
      commentCounts.hide()
      switch @$(".forum-nav-sort-control").val()
        when "date", "comments"
          commentCounts.show()
        when "votes"
          voteCounts.show()

    renderMorePages: ->
      if @displayedCollection.hasMorePages()
        @$(".forum-nav-thread-list").append("<li class='forum-nav-load-more'><a href='#' class='forum-nav-load-more-link'>" + gettext("Load more") + "</a></li>")

    getLoadingContent: (srText) ->
      return '<div class="forum-nav-loading" tabindex="0"><span class="icon-spinner icon-spin"/><span class="sr" role="alert">' + srText + '</span></div>'

    loadMorePages: (event) =>
      if event
        event.preventDefault()
      loadMoreElem = @$(".forum-nav-load-more")
      loadMoreElem.html(@getLoadingContent(gettext("Loading more threads")))
      loadingElem = loadMoreElem.find(".forum-nav-loading")
      DiscussionUtil.makeFocusTrap(loadingElem)
      loadingElem.focus()
      options = {}
      switch @mode
        when 'search'
          options.search_text = @current_search
          if @group_id
            options.group_id = @group_id          
        when 'followed'
          options.user_id = window.user.id
          options.group_id = "all"
        when 'commentables'
          options.commentable_ids = @discussionIds
          if @group_id
            options.group_id = @group_id
        when 'all'
          if @group_id
            options.group_id = @group_id
        
    
      lastThread = @collection.last()?.get('id')
      if lastThread
        # Pagination; focus the first thread after what was previously the last thread
        @once("threads:rendered", ->
          $(".forum-nav-thread[data-id='#{lastThread}'] + .forum-nav-thread .forum-nav-thread-link").focus()
        )
      else
        # Totally refreshing the list (e.g. from clicking a sort button); focus the first thread
        @once("threads:rendered", ->
          $(".forum-nav-thread-link").first()?.focus()
        )

      error = =>
        @renderThreads()
        DiscussionUtil.discussionAlert(gettext("Sorry"), gettext("We had some trouble loading more threads. Please try again."))

      @collection.retrieveAnotherPage(@mode, options, {sort_key: @$(".forum-nav-sort-control").val()}, error)

    renderThread: (thread) =>
      content = $(_.template($("#thread-list-item-template").html())(thread.toJSON()))
      unreadCount = thread.get('unread_comments_count') + (if thread.get("read") then 0 else 1)
      if unreadCount > 0
        content.find('.forum-nav-thread-comments-count').attr(
          "data-tooltip",
          interpolate(
            ngettext('%(unread_count)s new comment', '%(unread_count)s new comments', unreadCount),
            {unread_count: unreadCount},
            true
          )
        )
      content

    threadSelected: (e) =>
      # Use .attr('data-id') rather than .data('id') because .data does type
      # coercion. Usually, this is fine, but when Mongo gives an object id with
      # no letters, it casts it to a Number.

      thread_id = $(e.target).closest(".forum-nav-thread").attr("data-id")
      @setActiveThread(thread_id)
      @trigger("thread:selected", thread_id)  # This triggers a callback in the DiscussionRouter which calls the line above...
      false

    threadRemoved: (thread_id) =>
      @trigger("thread:removed", thread_id)

    setActiveThread: (thread_id) ->
      @$(".forum-nav-thread[data-id!='#{thread_id}'] .forum-nav-thread-link").removeClass("is-active")
      @$(".forum-nav-thread[data-id='#{thread_id}'] .forum-nav-thread-link").addClass("is-active")

    showSearch: ->
      @$(".browse").removeClass('is-dropped')
      @hideTopicDrop()

      @$(".search").addClass('is-open')
      @$(".browse").removeClass('is-open')
      setTimeout (-> @$(".post-search-field").focus()), 200 unless @$(".post-search-field").is(":focus")

    goHome: ->
      @template = _.template($("#discussion-home").html())
      $(".discussion-column").html(@template)
      $(".forum-nav-thread-list a").removeClass("is-active")
      $("input.email-setting").bind "click", @updateEmailNotifications
      url = DiscussionUtil.urlFor("notifications_status",window.user.get("id"))
      DiscussionUtil.safeAjax
          url: url
          type: "GET"
          success: (response, textStatus) =>
            if response.status
              $('input.email-setting').attr('checked','checked')
            else
              $('input.email-setting').removeAttr('checked')
      thread_id = null
      @trigger("thread:removed")  
      #select all threads


    toggleTopicDrop: (event) =>
      event.preventDefault()
      event.stopPropagation()
      if @current_search != ""
        @clearSearch()
      @$(".search").removeClass('is-open')
      @$(".browse").addClass('is-open')
      @$(".browse").toggleClass('is-dropped')

      if @$(".browse").hasClass('is-dropped')
        @$(".browse-topic-drop-menu-wrapper").show()
        $(".browse-topic-drop-search-input").focus()
        $("body").bind "click", @toggleTopicDrop
        $("body").bind "keydown", @setActiveItem
      else
        @hideTopicDrop()

    hideTopicDrop: ->
      @$(".browse-topic-drop-menu-wrapper").hide()
      $("body").unbind "click", @toggleTopicDrop
      $("body").unbind "keydown", @setActiveItem

    # TODO get rid of this asap
    setTopicHack: (boardNameContainer) ->
      item = $(boardNameContainer).closest('a')
      boardName = item.find(".board-name").html()
      _.each item.parents('ul').not('.browse-topic-drop-menu'), (parent) ->
        boardName = $(parent).siblings('a').find('.board-name').html() + ' / ' + boardName
      @$(".current-board").html(@fitName(boardName))

    setTopic: (event) ->
      item = $(event.target).closest('a')
      boardName = item.find(".board-name").html()
      _.each item.parents('ul').not('.browse-topic-drop-menu'), (parent) ->
        boardName = $(parent).siblings('a').find('.board-name').html() + ' / ' + boardName
      @$(".current-board").html(@fitName(boardName))

    setSelectedTopic: (name) ->
      @$(".current-board").html(@fitName(name))

    getNameWidth: (name) ->
      test = $("<div>")
      test.css
        "font-size": @$(".current-board").css('font-size')
        opacity: 0
        position: 'absolute'
        left: -1000
        top: -1000
      $("body").append(test)
      test.html(name)
      width = test.width()
      test.remove()
      return width

    fitName: (name) ->
      @maxNameWidth = (@$el.width() * .8) - 50
      width = @getNameWidth(name)
      if width < @maxNameWidth
        return name
      path = (x.replace /^\s+|\s+$/g, "" for x in name.split("/"))
      while path.length > 1
        path.shift()
        partialName = gettext("…") + "/" + path.join("/")
        if  @getNameWidth(partialName) < @maxNameWidth
          return partialName
      rawName = path[0]
      name = gettext("…") + "/" + rawName
      while @getNameWidth(name) > @maxNameWidth
        rawName = rawName[0...rawName.length-1]
        name =  gettext("…") + "/" + rawName + gettext("…")
      return name

    filterTopic: (event) ->
      if @current_search != ""
        @setTopic(event)
        @clearSearch @filterTopic, event
      else
        @setTopic(event)  # just sets the title for the dropdown
        item = $(event.target).closest('li')
        discussionId = item.find("span.board-name").data("discussion_id")
        if discussionId == "#all"
          @discussionIds = ""
          @$(".post-search-field").val("")
          @$('.forum-nav-filter-cohort').show()
          @retrieveAllThreads()
        else if discussionId == "#flagged"
          @discussionIds = ""
          @$(".post-search-field").val("")
          @$('.forum-nav-filter-cohort').hide()
          @retrieveFlaggedThreads() 
        else if discussionId == "#following"
          @retrieveFollowed(event)
          @$('.forum-nav-filter-cohort').hide()
        else
          discussionIds = _.map item.find(".board-name[data-discussion_id]"), (board) -> $(board).data("discussion_id").id
          
          if $(event.target).attr('cohorted') == "True"
            @retrieveDiscussions(discussionIds, "function(){$('.forum-nav-filter-cohort').show();}")
          else
            @retrieveDiscussions(discussionIds, "function(){$('.forum-nav-filter-cohort').hide();}")
    
    chooseCohort: (event) ->
      @group_id = @$('.forum-nav-filter-cohort-control :selected').val()
      @collection.current_page = 0
      @collection.reset()
      @loadMorePages(event)
      
    retrieveDiscussion: (discussion_id, callback=null) ->
      url = DiscussionUtil.urlFor("retrieve_discussion", discussion_id)
      DiscussionUtil.safeAjax
        url: url
        type: "GET"
        success: (response, textStatus) =>
          @collection.current_page = response.page
          @collection.pages = response.num_pages
          @collection.reset(response.discussion_data)
          Content.loadContentInfos(response.annotated_content_info)
          @displayedCollection.reset(@collection.models)# Don't think this is necessary because it's called on collection.reset
          if callback?
            callback()

    
    retrieveDiscussions: (discussion_ids) ->
      @discussionIds = discussion_ids.join(',')
      @mode = 'commentables'
      @retrieveFirstPage()

    retrieveAllThreads: () ->
      @mode = 'all'
      @retrieveFirstPage()

    retrieveFirstPage: (event)->
      @collection.current_page = 0
      @collection.reset()
      @loadMorePages(event)

    retrieveFlaggedThreads: (event)->
      @collection.current_page = 0
      @collection.reset()
      @mode = 'flagged'
      @loadMorePages(event)

    sortThreads: (event) ->
      @displayedCollection.setSortComparator(@$(".forum-nav-sort-control").val())

      @retrieveFirstPage(event)

    performSearch: (event) ->
      if event.which == 13
        event.preventDefault()
        text = @$(".post-search-field").val()
        @searchFor(text)

    searchFor: (text, callback, value) ->
      @clearSearchAlerts()
      @mode = 'search'
      @current_search = text
      url = DiscussionUtil.urlFor("search")
      #TODO: This might be better done by setting discussion.current_page=0 and calling discussion.loadMorePages
      # Mainly because this currently does not reset any pagination variables which could cause problems.
      # This doesn't use pagination either.
      DiscussionUtil.safeAjax
        $elem: @$(".post-search-field")
        data: { text: text }
        url: url
        type: "GET"
        dataType: 'json'
        $loading: $
        loadingCallback: =>
          @$(".forum-nav-thread-list").html("<li class='forum-nav-load-more'>" + @getLoadingContent(gettext("Loading thread list")) + "</li>")
        loadedCallback: =>
          if callback
            callback.apply @, [value]
        success: (response, textStatus) =>
          if textStatus == 'success'
            # TODO: Augment existing collection?
            @collection.reset(response.discussion_data)
            Content.loadContentInfos(response.annotated_content_info)
            @collection.current_page = response.page
            @collection.pages = response.num_pages
            if !_.isNull response.corrected_text
              message = interpolate(
                _.escape(gettext('No results found for %(original_query)s. Showing results for %(suggested_query)s.')),
                {"original_query": "<em>" + _.escape(text) + "</em>", "suggested_query": "<em>" + response.corrected_text + "</em>"},
                true
              )
              @addSearchAlert(message)
            else if response.discussion_data.length == 0
              @addSearchAlert(gettext('No threads matched your query.'))
            # TODO: Perhaps reload user info so that votes can be updated.
            # In the future we might not load all of a user's votes at once
            # so this would probably be necessary anyway
            @displayedCollection.reset(@collection.models) # Don't think this is necessary
            @searchForUser(text) if text


    searchForUser: (text) ->
      DiscussionUtil.safeAjax
        data: { username: text }
        url: DiscussionUtil.urlFor("users")
        type: "GET"
        dataType: 'json'
        error: =>
          return
        success: (response) =>
          if response.users.length > 0
            message = interpolate(
              _.escape(gettext('Show posts by %(username)s.')),
              {"username":
                _.template('<a class="link-jump" href="<%= url %>"><%- username %></a>', {
                  url: DiscussionUtil.urlFor("user_profile", response.users[0].id),
                  username: response.users[0].username
                })
              },
              true
            )
            @addSearchAlert(message)

    clearSearch: (callback, value) ->
      @$(".post-search-field").val("")
      @searchFor("", callback, value)

    setActiveItem: (event) ->
      if event.which == 13
        $(".browse-topic-drop-menu-wrapper .focused").click()
        return
      if event.which != 40 && event.which != 38
        return

      event.preventDefault()

      items = $.makeArray($(".browse-topic-drop-menu-wrapper a").not(".hidden"))
      index = items.indexOf($('.browse-topic-drop-menu-wrapper .focused')[0])

      if event.which == 40
          index = Math.min(index + 1, items.length - 1)
      if event.which == 38
          index = Math.max(index - 1, 0)

      $(".browse-topic-drop-menu-wrapper .focused").removeClass("focused")
      $(items[index]).addClass("focused")

      itemTop = $(items[index]).parent().offset().top
      scrollTop = $(".browse-topic-drop-menu").scrollTop()
      itemFromTop = $(".browse-topic-drop-menu").offset().top - itemTop
      scrollTarget = Math.min(scrollTop - itemFromTop, scrollTop)
      scrollTarget = Math.max(scrollTop - itemFromTop - $(".browse-topic-drop-menu").height() + $(items[index]).height(), scrollTarget)
      $(".browse-topic-drop-menu").scrollTop(scrollTarget)

    retrieveFollowed: (event)=>
      @mode = 'followed'
      @retrieveFirstPage(event)

    updateEmailNotifications: () =>
      if $('input.email-setting').attr('checked')
        DiscussionUtil.safeAjax
          url: DiscussionUtil.urlFor("enable_notifications")
          type: "POST"
          error: () =>
            $('input.email-setting').removeAttr('checked')
      else
        DiscussionUtil.safeAjax
          url: DiscussionUtil.urlFor("disable_notifications")
          type: "POST"
          error: () =>
            $('input.email-setting').attr('checked','checked')


