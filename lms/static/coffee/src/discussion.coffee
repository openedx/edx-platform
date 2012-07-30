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
      watch_commentable   : "/courses/#{$$course_id}/discussion/#{param}/watch"
      unwatch_commentable : "/courses/#{$$course_id}/discussion/#{param}/unwatch"
      create_thread       : "/courses/#{$$course_id}/discussion/#{param}/threads/create"
      update_thread       : "/courses/#{$$course_id}/discussion/threads/#{param}/update"
      create_comment      : "/courses/#{$$course_id}/discussion/threads/#{param}/reply"
      delete_thread       : "/courses/#{$$course_id}/discussion/threads/#{param}/delete"
      upvote_thread       : "/courses/#{$$course_id}/discussion/threads/#{param}/upvote"
      downvote_thread     : "/courses/#{$$course_id}/discussion/threads/#{param}/downvote"
      watch_thread        : "/courses/#{$$course_id}/discussion/threads/#{param}/watch"
      unwatch_thread      : "/courses/#{$$course_id}/discussion/threads/#{param}/unwatch"
      update_comment      : "/courses/#{$$course_id}/discussion/comments/#{param}/update"
      endorse_comment     : "/courses/#{$$course_id}/discussion/comments/#{param}/endorse"
      create_sub_comment  : "/courses/#{$$course_id}/discussion/comments/#{param}/reply"
      delete_comment      : "/courses/#{$$course_id}/discussion/comments/#{param}/delete"
      upvote_comment      : "/courses/#{$$course_id}/discussion/comments/#{param}/upvote"
      downvote_comment    : "/courses/#{$$course_id}/discussion/comments/#{param}/downvote"
      upload              : "/courses/#{$$course_id}/discussion/upload"
      search              : "/courses/#{$$course_id}/discussion/forum/search"
      tags_autocomplete   : "/courses/#{$$course_id}/discussion/threads/tags/autocomplete"
    }[name]

  handleAnchorAndReload: (response) ->
    #window.location = window.location.pathname + "#" + response['id']
    window.location.reload()

  initializeDiscussion: (discussion) ->

    initializeVote = (index, content) ->
      $content = $(content)
      $local = generateLocal($content.children(".discussion-content"))
      id = $content.attr("_id")
      if id in $$user_info.upvoted_ids
        $local(".discussion-vote-up").addClass("voted")
      else if id in $$user_info.downvoted_ids
        $local(".discussion-vote-down").addClass("voted")

    initializeWatchDiscussion = (discussion) ->
      $discussion = $(discussion)
      id = $discussion.attr("_id")
      $local = generateLocal($discussion.children(".discussion-non-content"))

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
        unwatchDiscussion = generateDiscussionLink("discussion-unwatch-discussion", "Unwatch", handleUnwatchDiscussion)
        $local(".discussion-title-wrapper").append(unwatchDiscussion)
      else
        watchDiscussion = generateDiscussionLink("discussion-watch-discussion", "Watch", handleWatchDiscussion)
        $local(".discussion-title-wrapper").append(watchDiscussion)

      newPostBody = $(discussion).find(".new-post-body")
      if newPostBody.length
        Markdown.makeWmdEditor newPostBody, "-new-post-body-#{$(discussion).attr('_id')}", Discussion.urlFor('upload')

    initializeWatchThreads = (index, thread) ->
      $thread = $(thread)
      id = $thread.attr("_id")
      $local = generateLocal($thread.children(".discussion-content"))

      handleWatchThread = (elem) ->
        url = Discussion.urlFor('watch_thread', id)
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

      
      if id in $$user_info.subscribed_thread_ids
        unwatchThread = generateDiscussionLink("discussion-unwatch-thread", "Unwatch", handleUnwatchThread)
        $local(".info").append(unwatchThread)
      else
        watchThread = generateDiscussionLink("discussion-watch-thread", "Watch", handleWatchThread)
        $local(".info").append(watchThread)

    $local = generateLocal(discussion)

    if $$user_info?
      $local(".comment").each(initializeVote)
      $local(".thread").each(initializeVote).each(initializeWatchThreads)
      initializeWatchDiscussion(discussion)

    if $$tags?
      $local(".new-post-tags").tagsInput
        autocomplete_url: Discussion.urlFor('tags_autocomplete')
        autocomplete:
          remoteDataType: 'json'
        interactive: true
        defaultText: "add a tag"
        height: "30px"
        removeWithBackspace: true

  bindContentEvents: (content) ->

    $content = $(content)
    $discussionContent = $content.children(".discussion-content")
    $local = generateLocal($discussionContent)

    id = $content.attr("_id")

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

        errorsField = $("<ul>").addClass("discussion-errors")
        editView.append(errorsField)

        textarea = $("<div>").addClass("comment-edit")
        editView.append(textarea)

        anonymousCheckbox = $("<input>").attr("type", "checkbox")
                                        .addClass("discussion-post-anonymously")
                                        .attr("id", "discussion-post-anonymously-#{id}")
        anonymousLabel = $("<label>").attr("for", "discussion-post-anonymously-#{id}")
                                     .html("post anonymously")
        editView.append(anonymousCheckbox).append(anonymousLabel)


        if $discussionContent.parent(".thread").attr("_id") not in $$user_info.subscribed_thread_ids
          watchCheckbox = $("<input>").attr("type", "checkbox")
                                      .addClass("discussion-auto-watch")
                                      .attr("id", "discussion-auto-watch-#{id}")
                                      .attr("checked", "")
          watchLabel = $("<label>").attr("for", "discussion-auto-watch-#{id}")
                                   .html("watch this thread")
          editView.append(watchCheckbox).append(watchLabel)
        
        $discussionContent.append(editView)

        Markdown.makeWmdEditor $local(".comment-edit"), "-comment-edit-#{id}", Discussion.urlFor('upload')
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
        url = Discussion.urlFor('create_comment', id)
      else if $content.hasClass("comment")
        url = Discussion.urlFor('create_sub_comment', id)
      else
        return

      body = $local("#wmd-input-comment-edit-#{id}").val()

      anonymous = false || $local(".discussion-post-anonymously").is(":checked")
      autowatch = false || $local(".discussion-auto-watch").is(":checked")

      $.post url, {body: body, anonymous: anonymous, autowatch: autowatch}, (response, textStatus) ->
        if response.errors
          errorsField = $local(".discussion-errors").empty()
          for error in response.errors
            errorsField.append($("<li>").addClass("new-post-form-error").html(error))
        else
          Discussion.handleAnchorAndReload(response)
      , 'json'

    handleVote = (elem, value) ->
      contentType = if $content.hasClass("thread") then "thread" else "comment"
      url = Discussion.urlFor("#{value}vote_#{contentType}", id)
      $.post url, {}, (response, textStatus) ->
        if textStatus == "success"
          Discussion.handleAnchorAndReload(response)
      , 'json'

    handleEditThread = (elem) ->

    handleEditComment = (elem) ->
          
    $local(".discussion-reply").click ->
      handleReply(this)

    $local(".discussion-cancel-reply").click ->
      handleCancelReply(this)

    $local(".discussion-vote-up").click ->
      handleVote(this, "up")

    $local(".discussion-vote-down").click ->
      handleVote(this, "down")

    $local(".discussion-edit").click ->
      if $content.hasClass("thread")
        handleEditThread(this)
      else
        handleEditComment(this)
      

  initializeContent: (content) ->
    $content = $(content)
    $local = generateLocal($content.children(".discussion-content"))
    raw_text = $local(".content-body").html()
    converter = Markdown.getMathCompatibleConverter()
    $local(".content-body").html(converter.makeHtml(raw_text))

  bindDiscussionEvents: (discussion) ->
    $discussion = $(discussion)
    $discussionNonContent = $discussion.children(".discussion-non-content")
    $local = generateLocal($discussionNonContent)#(selector) -> $discussionNonContent.find(selector)

    id = $discussion.attr("_id")

    handleSearch = (text, isSearchWithinBoard) ->
      if text.length
        if $local(".discussion-search-within-board").is(":checked")
          window.location = window.location.pathname + '?text=' + encodeURI(text)
        else
          window.location = Discussion.urlFor('search') + '?text=' + encodeURI(text)

    handleSubmitNewThread = (elem) ->
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
    
    $local(".discussion-search-form").submit (event) ->
      event.preventDefault()
      text = $local(".search-input").val()
      isSearchWithinBoard = $local(".discussion-search-within-board").is(":checked")
      handleSearch(text, isSearchWithinBoard)

    $local(".discussion-new-post").click ->
      handleSubmitNewThread(this)

    $local(".discussion-search").click ->
      $local(".new-post-form").submit()

    $discussion.find(".thread").each (index, thread) ->
      Discussion.initializeContent(thread)
      Discussion.bindContentEvents(thread)

    $discussion.find(".comment").each (index, comment) ->
      Discussion.initializeContent(comment)
      Discussion.bindContentEvents(comment)
