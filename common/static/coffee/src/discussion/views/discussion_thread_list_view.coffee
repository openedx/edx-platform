if Backbone?
  class @DiscussionThreadListView extends Backbone.View
    events:
      "click .forum-nav-browse": "toggleBrowseMenu"
      "keypress .forum-nav-browse-filter-input": (event) => DiscussionUtil.ignoreEnterKey(event)
      "keyup .forum-nav-browse-filter-input": "filterTopics"
      "click .forum-nav-browse-menu-wrapper": "ignoreClick"
      "click .forum-nav-browse-title": "selectTopic"
      "keydown .forum-nav-search-input": "performSearch"
      "change .forum-nav-sort-control": "sortThreads"
      "click .forum-nav-thread-link": "threadSelected"
      "click .forum-nav-load-more-link": "loadMorePages"
      "change .forum-nav-filter-main-control": "chooseFilter"
      "change .forum-nav-filter-cohort-control": "chooseCohort"

    initialize: (options) ->
      @courseSettings = options.courseSettings
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
      menuItem = @$(".forum-nav-browse-menu-item[data-discussion-id]").filter(-> $(this).data("discussion-id") == commentable_id)
      @setCurrentTopicDisplay(@getPathText(menuItem))
      @retrieveDiscussion commentable_id, =>
        @trigger "thread:created", thread.get('id')

    updateSidebar: =>

      scrollTop = $(window).scrollTop();
      windowHeight = $(window).height();

      discussionBody = $(".discussion-column")
      discussionsBodyTop = if discussionBody[0] then discussionBody.offset().top
      discussionsBodyBottom = discussionsBodyTop + discussionBody.outerHeight()

      sidebar = $(".forum-nav")
      if scrollTop > discussionsBodyTop - @sidebar_padding
        sidebar.css('top', scrollTop - discussionsBodyTop + @sidebar_padding);
      else
        sidebar.css('top', '0');

      sidebarHeight = windowHeight - Math.max(discussionsBodyTop - scrollTop, @sidebar_padding)

      topOffset = scrollTop + windowHeight
      discussionBottomOffset = discussionsBodyBottom + @sidebar_padding
      amount = Math.max(topOffset - discussionBottomOffset, 0)

      sidebarHeight = sidebarHeight - @sidebar_padding - amount
      sidebarHeight = Math.min(sidebarHeight + 1, discussionBody.outerHeight())
      sidebar.css 'height', sidebarHeight

      headerHeight = @$(".forum-nav-header").outerHeight()
      refineBarHeight = @$(".forum-nav-refine-bar").outerHeight()
      browseFilterHeight = @$(".forum-nav-browse-filter").outerHeight()
      @$('.forum-nav-thread-list').css('height', (sidebarHeight - headerHeight - refineBarHeight - 2) + 'px')
      @$('.forum-nav-browse-menu').css('height', (sidebarHeight - headerHeight - browseFilterHeight - 2) + 'px')


    # Because we want the behavior that when the body is clicked the menu is
    # closed, we need to stop propagation of a click in any part of the menu
    # that is not a link.
    ignoreClick: (event) ->
        event.stopPropagation()

    render: ->
      @timer = 0
      @$el.html(
        @template({
          isCohorted: @courseSettings.get("is_cohorted"),
          isPrivilegedUser: DiscussionUtil.isPrivilegedUser()
        })
      )
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
      options = {filter: @filter}
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

    goHome: ->
      @template = _.template($("#discussion-home").html())
      $(".forum-content").html(@template)
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

    isBrowseMenuVisible: =>
      @$(".forum-nav-browse-menu-wrapper").is(":visible")

    showBrowseMenu: =>
      if not @isBrowseMenuVisible()
        @$(".forum-nav-browse").addClass("is-active")
        @$(".forum-nav-browse-menu-wrapper").show()
        @$(".forum-nav-thread-list-wrapper").hide()
        $(".forum-nav-browse-filter-input").focus()
        $("body").bind "click", @hideBrowseMenu
        @updateSidebar()

    hideBrowseMenu: =>
      if @isBrowseMenuVisible()
        @$(".forum-nav-browse").removeClass("is-active")
        @$(".forum-nav-browse-menu-wrapper").hide()
        @$(".forum-nav-thread-list-wrapper").show()
        $("body").unbind "click", @hideBrowseMenu
        @updateSidebar()

    toggleBrowseMenu: (event) =>
      event.preventDefault()
      event.stopPropagation()

      if @isBrowseMenuVisible()
        @hideBrowseMenu()
      else
        @showBrowseMenu()

    # Given a menu item, get the text for it and its ancestors
    # (starting from the root, separated by " / ")
    getPathText: (item) ->
      path = item.parents(".forum-nav-browse-menu-item").andSelf()
      pathTitles = path.children(".forum-nav-browse-title").map((i, elem) -> $(elem).text()).get()
      pathText = pathTitles.join(" / ")

    filterTopics: (event) =>
      query = $(event.target).val()
      items = @$(".forum-nav-browse-menu-item")
      if query.length == 0
        items.show()
      else
        # If all filter terms occur in the path to an item then that item and
        # all its descendants are displayed
        items.hide()
        items.each (i, item) =>
          item = $(item)
          if not item.is(":visible")
            pathText = @getPathText(item).toLowerCase()
            if query.split(" ").every((term) -> pathText.search(term.toLowerCase()) != -1)
              path = item.parents(".forum-nav-browse-menu-item").andSelf()
              path.add(item.find(".forum-nav-browse-menu-item")).show()

    setCurrentTopicDisplay: (text) ->
      @$(".forum-nav-browse-current").text(@fitName(text))

    getNameWidth: (name) ->
      test = $("<div>")
      test.css
        "font-size": @$(".forum-nav-browse-current").css('font-size')
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
      @maxNameWidth = @$(".forum-nav-browse").width() -
        parseInt(@$(".forum-nav-browse").css("padding-left")) -
        parseInt(@$(".forum-nav-browse").css("padding-right")) -
        @$(".forum-nav-browse .icon").outerWidth(true) -
        @$(".forum-nav-browse-drop-arrow").outerWidth(true)
      width = @getNameWidth(name)
      if width < @maxNameWidth
        return name
      path = (x.replace /^\s+|\s+$/g, "" for x in name.split("/"))
      prefix = ""
      while path.length > 1
        prefix = gettext("…") + "/"
        path.shift()
        partialName = prefix + path.join("/")
        if  @getNameWidth(partialName) < @maxNameWidth
          return partialName
      rawName = path[0]
      name = prefix + rawName
      while @getNameWidth(name) > @maxNameWidth
        rawName = rawName[0...rawName.length-1]
        name =  prefix + rawName + gettext("…")
      return name

    selectTopic: (event) ->
      event.preventDefault()
      @hideBrowseMenu()
      @clearSearch()

      item = $(event.target).closest('.forum-nav-browse-menu-item')
      @setCurrentTopicDisplay(@getPathText(item))
      if item.hasClass("forum-nav-browse-menu-all")
        @discussionIds = ""
        @$('.forum-nav-filter-cohort').show()
        @retrieveAllThreads()
      else if item.hasClass("forum-nav-browse-menu-following")
        @retrieveFollowed()
        @$('.forum-nav-filter-cohort').hide()
      else
        allItems = item.find(".forum-nav-browse-menu-item").andSelf()
        discussionIds = allItems.filter("[data-discussion-id]").map(
          (i, elem) -> $(elem).data("discussion-id")
        ).get()
        @retrieveDiscussions(discussionIds)
        @$(".forum-nav-filter-cohort").toggle(item.data('cohorted') == true)

    chooseFilter: (event) =>
      @filter = $(".forum-nav-filter-main-control :selected").val()
      @retrieveFirstPage()

    chooseCohort: (event) =>
      @group_id = @$('.forum-nav-filter-cohort-control :selected').val()
      @retrieveFirstPage()
      
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

    sortThreads: (event) ->
      @displayedCollection.setSortComparator(@$(".forum-nav-sort-control").val())

      @retrieveFirstPage(event)

    performSearch: (event) ->
      if event.which == 13
        event.preventDefault()
        @hideBrowseMenu()
        @setCurrentTopicDisplay(gettext("Search Results"))
        text = @$(".forum-nav-search-input").val()
        @searchFor(text)

    searchFor: (text) ->
      @clearSearchAlerts()
      @clearFilters()
      @mode = 'search'
      @current_search = text
      url = DiscussionUtil.urlFor("search")
      #TODO: This might be better done by setting discussion.current_page=0 and calling discussion.loadMorePages
      # Mainly because this currently does not reset any pagination variables which could cause problems.
      # This doesn't use pagination either.
      DiscussionUtil.safeAjax
        $elem: @$(".forum-nav-search-input")
        data: { text: text }
        url: url
        type: "GET"
        dataType: 'json'
        $loading: $
        loadingCallback: =>
          @$(".forum-nav-thread-list").html("<li class='forum-nav-load-more'>" + @getLoadingContent(gettext("Loading thread list")) + "</li>")
        loadedCallback: =>
          @$(".forum-nav-thread-list .forum-nav-load-more").remove()
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

    clearSearch: ->
      @$(".forum-nav-search-input").val("")
      @current_search = ""
      @clearSearchAlerts()

    clearFilters: ->
     @$(".forum-nav-filter-main-control").val("all")
     @$(".forum-nav-filter-cohort-control").val("all")

    retrieveFollowed: () =>
      @mode = 'followed'
      @retrieveFirstPage()

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


