if not @Discussion?
  @Discussion = {}

Discussion = @Discussion

@Discussion = $.extend @Discussion,

  initializeDiscussion: (discussion) ->

    initializeVote = (index, content) ->
      $content = $(content)
      $local = Discussion.generateLocal($content.children(".discussion-content"))
      id = $content.attr("_id")
      if id in $$user_info.upvoted_ids
        $local(".discussion-vote-up").addClass("voted")
      else if id in $$user_info.downvoted_ids
        $local(".discussion-vote-down").addClass("voted")

    initializeWatchDiscussion = (discussion) ->
      $discussion = $(discussion)
      id = $discussion.attr("_id")
      $local = Discussion.generateLocal($discussion.children(".discussion-non-content"))

      handleWatchDiscussion = (elem) ->
        url = Discussion.urlFor('watch_commentable', id)
        $.post url, {}, (response, textStatus) ->
          if textStatus == "success"
            Discussion.handleAnchorAndReload(response)
        , 'json'

      handleUnwatchDiscussion = (elem) ->
        url = Discussion.urlFor('unwatch_commentable', id)
        $.post url, {}, (response, textStatus) ->
          if textStatus == "success"
            Discussion.handleAnchorAndReload(response)
        , 'json'

      if id in $$user_info.subscribed_commentable_ids
        unwatchDiscussion = Discussion.generateDiscussionLink("discussion-unwatch-discussion", "Unwatch", handleUnwatchDiscussion)
        $local(".discussion-title-wrapper").append(unwatchDiscussion)
      else
        watchDiscussion = Discussion.generateDiscussionLink("discussion-watch-discussion", "Watch", handleWatchDiscussion)
        $local(".discussion-title-wrapper").append(watchDiscussion)

    initializeWatchThreads = (index, thread) ->
      $thread = $(thread)
      id = $thread.attr("_id")
      $local = Discussion.generateLocal($thread.children(".discussion-content"))

      handleWatchThread = (elem) ->
        $elem = $(elem)
        url = Discussion.urlFor('watch_thread', id)
        Discussion.safeAjax
          $elem: $elem
          url: url
          type: "POST"
          success: (response, textStatus) ->
            if textStatus == "success"
              $elem.removeClass("discussion-watch-thread")
                   .addClass("discussion-unwatch-thread")
                   .html("Unfollow")
                   .unbind('click').click ->
                     handleUnwatchThread(this)
          dataType: 'json'

      handleUnwatchThread = (elem) ->
        $elem = $(elem)
        url = Discussion.urlFor('unwatch_thread', id)
        Discussion.safeAjax
          $elem: $elem
          url: url
          type: "POST"
          success: (response, textStatus) ->
            if textStatus == "success"
              $elem.removeClass("discussion-unwatch-thread")
                   .addClass("discussion-watch-thread")
                   .html("Follow")
                   .unbind('click').click ->
                     handleWatchThread(this)
          dataType: 'json'

      if id in $$user_info.subscribed_thread_ids
        unwatchThread = Discussion.generateDiscussionLink("discussion-unwatch-thread", "Unfollow", handleUnwatchThread)
        $local(".info").append(unwatchThread)
      else
        watchThread = Discussion.generateDiscussionLink("discussion-watch-thread", "Follow", handleWatchThread)
        $local(".info").append(watchThread)

    $local = Discussion.generateLocal(discussion)

    if $$user_info?
      $local(".comment").each(initializeVote)
      $local(".thread").each(initializeVote).each(initializeWatchThreads)
      #initializeWatchDiscussion(discussion) TODO move this somewhere else

    $local(".new-post-tags").tagsInput
      autocomplete_url: Discussion.urlFor('tags_autocomplete')
      autocomplete:
        remoteDataType: 'json'
      interactive: true
      defaultText: "Tag your post"
      height: "30px"
      width: "90%"
      removeWithBackspace: true

  bindDiscussionEvents: (discussion) ->
    $discussion = $(discussion)
    $discussionNonContent = $discussion.children(".discussion-non-content")
    $local = Discussion.generateLocal($discussionNonContent)#(selector) -> $discussionNonContent.find(selector)

    id = $discussion.attr("_id")

    handleSearch = (text, isSearchWithinBoard) ->
      if text.length
        if $local(".discussion-search-within-board").is(":checked")
          window.location = window.location.pathname + '?text=' + encodeURI(text)
        else
          window.location = Discussion.urlFor('search') + '?text=' + encodeURI(text)

    handleSubmitNewPost = (elem) ->
      title = $local(".new-post-title").val()
      body = $local("#wmd-input-new-post-body-#{id}").val()
      tags = $local(".new-post-tags").val()
      url = Discussion.urlFor('create_thread', $local(".new-post-form").attr("_id"))
      $.post url, {title: title, body: body, tags: tags}, (response, textStatus) ->
        if response.errors
          errorsField = $local(".discussion-errors").empty()
          for error in response.errors
            errorsField.append($("<li>").addClass("new-post-form-error").html(error))
        else
          Discussion.handleAnchorAndReload(response)
      , 'json'

    handleCancelNewPost = (elem) ->
      $local(".new-post-form").hide()
      $local(".discussion-new-post").show()

    handleNewPost = (elem) ->
      newPostForm = $local(".new-post-form")
      if newPostForm.length
        newPostForm.show()
        $(elem).hide()
      else
        view = {
          discussion_id: id
        }
        $discussionNonContent.append Mustache.render Discussion.newPostTemplate, view
        newPostBody = $(discussion).find(".new-post-body")
        if newPostBody.length
          Markdown.makeWmdEditor newPostBody, "-new-post-body-#{$(discussion).attr('_id')}", Discussion.urlFor('upload')
        $local(".new-post-tags").tagsInput
          autocomplete_url: Discussion.urlFor('tags_autocomplete')
          autocomplete:
            remoteDataType: 'json'
          interactive: true
          defaultText: "Tag your post: press enter after each tag"
          height: "30px"
          width: "100%"
          removeWithBackspace: true
        $local(".discussion-submit-post").click ->
          handleSubmitNewPost(this)
        $local(".discussion-cancel-post").click ->
          handleCancelNewPost(this)
        $(elem).hide()

    handleAjaxSearch = (elem) ->
      $elem = $(elem)
      $discussionModule = $elem.parents(".discussion-module")
      $discussion = $discussionModule.find(".discussion")
      Discussion.safeAjax
        $elem: $elem
        url: $elem.attr("action")
        data:
          text: $local(".search-input").val()
        type: "GET"
        success: (data, textStatus) ->
          $discussion.replaceWith(data)
          $discussion = $discussionModule.find(".discussion")
          Discussion.initializeDiscussion($discussion)
          Discussion.bindDiscussionEvents($discussion)
        dataType: 'html'

    handleAjaxSort = (elem) ->
      $elem = $(elem)
      $discussionModule = $elem.parents(".discussion-module")
      $discussion = $discussionModule.find(".discussion")
      Discussion.safeAjax
        $elem: $elem
        url: $elem.attr("sort-url")
        type: "GET"
        success: (data, textStatus) ->
          $discussion.replaceWith(data)
          $discussion = $discussionModule.find(".discussion")
          Discussion.initializeDiscussion($discussion)
          Discussion.bindDiscussionEvents($discussion)
        dataType: 'html'
    
    $local(".search-wrapper-forum > .discussion-search-form").submit (event) ->
      event.preventDefault()
      text = $local(".search-input").val()
      isSearchWithinBoard = $local(".discussion-search-within-board").is(":checked")
      handleSearch(text, isSearchWithinBoard)

    $local(".discussion-new-post").click ->
      handleNewPost(this)

    $local(".discussion-search-link").click ->
      handleAjaxSearch(this)

    $local(".search-wrapper-inline > .discussion-search-form").submit (e)->
      e.preventDefault()
      handleAjaxSearch(this)

    $local(".discussion-inline-sort-link").click ->
      handleAjaxSort(this)


    $discussion.find(".thread").each (index, thread) ->
      Discussion.initializeContent(thread)
      Discussion.bindContentEvents(thread)

    $discussion.find(".comment").each (index, comment) ->
      Discussion.initializeContent(comment)
      Discussion.bindContentEvents(comment)
