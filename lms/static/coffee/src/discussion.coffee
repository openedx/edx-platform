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

Discussion =

  urlFor: (name, param) ->
    {
      create_thread      : "/discussions/#{param}/threads/create"
      update_thread      : "/discussions/threads/#{param}/update"
      create_comment     : "/discussions/threads/#{param}/reply"
      delete_thread      : "/discussions/threads/#{param}/delete"
      update_comment     : "/discussions/comments/#{param}/update"
      endorse_comment    : "/discussions/comments/#{param}/endorse"
      create_sub_comment : "/discussions/comments/#{param}/reply"
      delete_comment     : "/discussions/comments/#{param}/delete"
      upvote_comment     : "/discussions/comments/#{param}/upvote"
      downvote_comment   : "/discussions/comments/#{param}/downvote"
      upvote_thread      : "/discussions/threads/#{param}/upvote"
      downvote_thread    : "/discussions/threads/#{param}/downvote"
      search             : "/discussions/forum/search"
    }[name]

  handleAnchorAndReload: (response) ->
    window.location = window.location.pathname + "#" + response['id']
    window.location.reload()

  bindContentEvents: (content) ->

    $content = $(content)
    $discussionContent = $content.children(".discussion-content")
    $local = (selector) -> $discussionContent.find(selector)

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

    generateDiscussionLink = (cls, txt, handler) ->
      $("<a>").addClass("discussion-link").
               attr("href", "javascript:void(0)").
               addClass(cls).html(txt).
               click(-> handler(this))

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

    $local(".discussion-reply").click ->
      handleReply(this)

    $local(".discussion-cancel-reply").click ->
      handleCancelReply(this)

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
