$ ->

  if $('#accordion').length
    active = $('#accordion ul:has(li.active)').index('#accordion ul')
    $('#accordion').bind('accordionchange', @log).accordion
      active: if active >= 0 then active else 1
      header: 'h3'
      autoHeight: false
    $('#open_close_accordion a').click @toggle
    $('#accordion').show()

  $("section.discussion").each (index, discussion) ->
    Discussion.bindDiscussionEvents(discussion)
    Discussion.initializeDiscussion(discussion)

generateLocal = (elem) ->
  (selector) -> $(elem).find(selector)

generateDiscussionLink = (cls, txt, handler) ->
  $("<a>").addClass("discussion-link").
           attr("href", "javascript:void(0)").
           addClass(cls).html(txt).
           click(-> handler(this))

Discussion =

  urlFor: (name, param) ->
    {
      watch_commentable   : "/discussions/#{param}/watch"
      unwatch_commentable : "/discussions/#{param}/unwatch"
      create_thread       : "/discussions/#{param}/threads/create"
      update_thread       : "/discussions/threads/#{param}/update"
      create_comment      : "/discussions/threads/#{param}/reply"
      delete_thread       : "/discussions/threads/#{param}/delete"
      upvote_thread       : "/discussions/threads/#{param}/upvote"
      downvote_thread     : "/discussions/threads/#{param}/downvote"
      watch_thread        : "/discussions/threads/#{param}/watch"
      unwatch_thread      : "/discussions/threads/#{param}/unwatch"
      update_comment      : "/discussions/comments/#{param}/update"
      endorse_comment     : "/discussions/comments/#{param}/endorse"
      create_sub_comment  : "/discussions/comments/#{param}/reply"
      delete_comment      : "/discussions/comments/#{param}/delete"
      upvote_comment      : "/discussions/comments/#{param}/upvote"
      downvote_comment    : "/discussions/comments/#{param}/downvote"
      search              : "/discussions/forum/search"
    }[name]

  handleAnchorAndReload: (response) ->
    #window.location = window.location.pathname + "#" + response['id']
    window.location.reload()

  initializeDiscussion: (discussion) ->
    initializeVote = (index, content) ->
      $content = $(content)
      $local = generateLocal($content.children(".discussion-content"))
      id = $content.attr("_id")
      if id in user_info.upvoted_ids
        $local(".discussion-vote-up").addClass("voted")
      else if id in user_info.downvoted_ids
        $local(".discussion-vote-down").addClass("voted")


    initializeWatchThreads = (index, thread) ->
      $thread = $(thread)
      id = $thread.attr("_id")
      $local = generateLocal($thread.children(".discussion-content"))

      handleWatchThread = (elem) ->
        url = Discussion.urlFor('watch_thread', id)
        console.log url
        $.post url, {}, (response, textStatus) ->
          if textStatus == "success"
            Discussion.handleAnchorAndReload(response)
        , 'json'

      handleUnwatchThread = (elem) ->
        url = Discussion.urlFor('unwatch_thread', id)
        $.post url, {}, (response, textStatus) ->
          if textStatus == "success"
            Discussion.handleAnchorAndReload(response)
        , 'json'

      if id in user_info.subscribed_thread_ids
        unwatchThread = generateDiscussionLink("discussion-unwatch-thread", "Unwatch", handleUnwatchThread)
        $local(".info").append(unwatchThread)
      else
        watchThread = generateDiscussionLink("discussion-watch-thread", "Watch", handleWatchThread)
        $local(".info").append(watchThread)

    if user_info?
      $(discussion).find(".comment").each(initializeVote)
      $(discussion).find(".thread").each(initializeVote).each(initializeWatchThreads)

  bindContentEvents: (content) ->

    $content = $(content)
    $discussionContent = $content.children(".discussion-content")
    $local = generateLocal($discussionContent)

    discussionContentHoverIn = ->
      status = $discussionContent.attr("status") || "normal"
      if status == "normal"
        $local(".discussion-link").show()
      else if status == "reply"
        $local(".discussion-cancel-reply").show()
        $local(".discussion-submit-reply").show()
      else if status == "edit"
        $local(".discussion-cancel-edit").show()
        $local(".discussion-update-edit").show()

    discussionContentHoverOut = ->
      $local(".discussion-link").hide()

    $discussionContent.hover(discussionContentHoverIn, discussionContentHoverOut)

    

    handleReply = (elem) ->
      editView = $local(".discussion-content-edit")
      if editView.length
        editView.show()
      else
        editView = $("<div>").addClass("discussion-content-edit")
        editView.append($("<textarea>").addClass("comment-edit"))
        $discussionContent.append(editView)
      cancelReply = generateDiscussionLink("discussion-cancel-reply", "Cancel", handleCancelReply)
      submitReply = generateDiscussionLink("discussion-submit-reply", "Submit", handleSubmitReply)
      $local(".discussion-link").hide()
      $(elem).after(submitReply).replaceWith(cancelReply)
      $discussionContent.attr("status", "reply")

    handleCancelReply = (elem) ->
      editView = $local(".discussion-content-edit")
      if editView.length
        editView.hide()
      $local(".discussion-submit-reply").remove()
      reply = generateDiscussionLink("discussion-reply", "Reply", handleReply)
      $local(".discussion-link").show()
      $(elem).replaceWith(reply)
      $discussionContent.attr("status", "normal")

    handleSubmitReply = (elem) ->
      if $content.hasClass("thread")
        url = Discussion.urlFor('create_comment', $content.attr("_id"))
      else if $content.hasClass("comment")
        url = Discussion.urlFor('create_sub_comment', $content.attr("_id"))
      else
        return
      body = $local(".comment-edit").val()
      $.post url, {body: body}, (response, textStatus) ->
        if textStatus == "success"
          Discussion.handleAnchorAndReload(response)
      , 'json'

    handleVote = (elem, value) ->
      contentType = if $content.hasClass("thread") then "thread" else "comment"
      url = Discussion.urlFor("#{value}vote_#{contentType}", $content.attr("_id"))
      $.post url, {}, (response, textStatus) ->
        if textStatus == "success"
          Discussion.handleAnchorAndReload(response)
      , 'json'
          
    $local(".discussion-reply").click ->
      handleReply(this)

    $local(".discussion-cancel-reply").click ->
      handleCancelReply(this)

    $local(".discussion-vote-up").click ->
      handleVote(this, "up")

    $local(".discussion-vote-down").click ->
      handleVote(this, "down")

  bindDiscussionEvents: (discussion) ->
    $discussion = $(discussion)
    $discussionNonContent = $discussion.children(".discussion-non-content")
    $local = (selector) -> $discussionNonContent.find(selector)

    handleSearch = (text, isSearchWithinBoard) ->
      if text.length
        if $local(".discussion-search-within-board").is(":checked")
          window.location = window.location.pathname + '?text=' + encodeURI(text)
        else
          window.location = Discussion.urlFor('search') + '?text=' + encodeURI(text)

    handleSubmitNewThread = (elem) ->
      title = $local(".new-post-title").val()
      body = $local(".new-post-body").val()
      url = Discussion.urlFor('create_thread', $local(".new-post-form").attr("_id"))
      $.post url, {title: title, body: body}, (response, textStatus) ->
        if textStatus == "success"
          Discussion.handleAnchorAndReload(response)
      , 'json'
    
    $local(".discussion-search-form").submit (event) ->
      event.preventDefault()
      text = $local(".discussion-search-text").val()
      isSearchWithinBoard = $local(".discussion-search-within-board").is(":checked")
      handleSearch(text, isSearchWithinBoard)

    $local(".discussion-new-post").click ->
      handleSubmitNewThread(this)

    $local(".discussion-search").click ->
      $local(".new-post-form").submit()

    $discussion.find(".thread").each (index, thread) ->
      Discussion.bindContentEvents(thread)

    $discussion.find(".comment").each (index, comment) ->
      Discussion.bindContentEvents(comment)
