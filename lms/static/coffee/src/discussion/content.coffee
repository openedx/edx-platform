if not @Discussion?
  @Discussion = {}

Discussion = @Discussion

@Discussion = $.extend @Discussion,

  bindContentEvents: (content) ->

    $content = $(content)
    $discussionContent = $content.children(".discussion-content")
    $local = Discussion.generateLocal($discussionContent)

    id = $content.attr("_id")

    discussionContentHoverIn = ->
      status = $discussionContent.attr("status") || "normal"
      if status == "normal"
        $local(".discussion-link").show()

    discussionContentHoverOut = ->
      $local(".discussion-link").hide()

    $discussionContent.hover(discussionContentHoverIn, discussionContentHoverOut)

    handleReply = (elem) ->
      $replyView = $local(".discussion-reply-new")
      if $replyView.length
        $replyView.show()
      else
        view = {
          id: id
          showWatchCheckbox: $discussionContent.parents(".thread").attr("_id") not in $$user_info.subscribed_thread_ids
        }
        $discussionContent.append Mustache.render Discussion.replyTemplate, view
        Markdown.makeWmdEditor $local(".reply-body"), "-reply-body-#{id}", Discussion.urlFor('upload')
        $local(".discussion-submit-post").click -> handleSubmitReply(this)
        $local(".discussion-cancel-post").click -> handleCancelReply(this)
      $local(".discussion-link").hide()
      $discussionContent.attr("status", "reply")

    handleCancelReply = (elem) ->
      $replyView = $local(".discussion-reply-new")
      if $replyView.length
        $replyView.hide()
      reply = Discussion.generateDiscussionLink("discussion-reply", "Reply", handleReply)
      $(elem).replaceWith(reply)
      $discussionContent.attr("status", "normal")

    handleSubmitReply = (elem) ->
      if $content.hasClass("thread")
        url = Discussion.urlFor('create_comment', id)
      else if $content.hasClass("comment")
        url = Discussion.urlFor('create_sub_comment', id)
      else
        return

      body = $local("#wmd-input-reply-body-#{id}").val()

      anonymous = false || $local(".discussion-post-anonymously").is(":checked")
      autowatch = false || $local(".discussion-auto-watch").is(":checked")

      Discussion.safeAjax
        url: url
        type: "POST"
        data:
          body: body
          anonymous: anonymous
          autowatch: autowatch
        success: (response, textStatus) ->
          if response.errors? and response.errors.length > 0
            errorsField = $local(".discussion-errors").empty()
            for error in response.errors
              errorsField.append($("<li>").addClass("new-post-form-error").html(error))
          else
            Discussion.handleAnchorAndReload(response)
        dataType: 'json'

    handleVote = (elem, value) ->
      contentType = if $content.hasClass("thread") then "thread" else "comment"
      url = Discussion.urlFor("#{value}vote_#{contentType}", id)
      $.post url, {}, (response, textStatus) ->
        if textStatus == "success"
          Discussion.handleAnchorAndReload(response)
      , 'json'

    handleCancelEdit = (elem) ->
      $local(".discussion-content-edit").hide()
      $local(".discussion-content-wrapper").show()

    handleEditThread = (elem) ->
      $local(".discussion-content-wrapper").hide()
      $editView = $local(".discussion-content-edit")
      if $editView.length
        $editView.show()
      else
        view = {
          id: id
          title: $local(".thread-title").html()
          body: $local(".thread-raw-body").html()
          tags: $local(".thread-raw-tags").html()
        }
        $discussionContent.append Mustache.render Discussion.editThreadTemplate, view
        Markdown.makeWmdEditor $local(".thread-body-edit"), "-thread-body-edit-#{id}", Discussion.urlFor('update_thread', id)
        $local(".thread-tags-edit").tagsInput
          autocomplete_url: Discussion.urlFor('tags_autocomplete')
          autocomplete:
            remoteDataType: 'json'
          interactive: true
          defaultText: "Tag your post: press enter after each tag"
          height: "30px"
          width: "100%"
          removeWithBackspace: true
        $local(".discussion-submit-update").unbind("click").click -> handleSubmitEditThread(this)
        $local(".discussion-cancel-update").unbind("click").click -> handleCancelEdit(this)

    handleSubmitEditThread = (elem) ->
      url = Discussion.urlFor('update_thread', id)
      title = $local(".thread-title-edit").val()
      body = $local("#wmd-input-thread-body-edit-#{id}").val()
      tags = $local(".thread-tags-edit").val()
      $.post url, {title: title, body: body, tags: tags}, (response, textStatus) ->
        if response.errors
          errorsField = $local(".discussion-update-errors").empty()
          for error in response.errors
            errorsField.append($("<li>").addClass("new-post-form-error").html(error))
        else
          Discussion.handleAnchorAndReload(response)
      , 'json'

    handleEditComment = (elem) ->
      $local(".discussion-content-wrapper").hide()
      $editView = $local(".discussion-content-edit")
      if $editView.length
        $editView.show()
      else
        view = {
          id: id
          body: $local(".comment-raw-body").html()
        }
        $discussionContent.append Mustache.render Discussion.editCommentTemplate, view
        Markdown.makeWmdEditor $local(".comment-body-edit"), "-comment-body-edit-#{id}", Discussion.urlFor('update_comment', id)
        $local(".discussion-submit-update").unbind("click").click -> handleSubmitEditComment(this)
        $local(".discussion-cancel-update").unbind("click").click -> handleCancelEdit(this)

    handleSubmitEditComment= (elem) ->
      url = Discussion.urlFor('update_comment', id)
      body = $local("#wmd-input-comment-body-edit-#{id}").val()
      $.post url, {body: body}, (response, textStatus) ->
        if response.errors
          errorsField = $local(".discussion-update-errors").empty()
          for error in response.errors
            errorsField.append($("<li>").addClass("new-post-form-error").html(error))
        else
          Discussion.handleAnchorAndReload(response)
      , 'json'

    handleEndorse = (elem) ->
      url = Discussion.urlFor('endorse_comment', id)
      endorsed = $local(".discussion-endorse").is(":checked")
      $.post url, {endorsed: endorsed}, (response, textStatus) ->
        # TODO error handling
        Discussion.handleAnchorAndReload(response)
      , 'json'

    handleHideSingleThread = (elem) ->
      $threadTitle = $local(".thread-title")
      $showComments = $local(".discussion-show-comments")
      $content.children(".comments").hide()
      $threadTitle.unbind('click').click handleShowSingleThread
      $showComments.unbind('click').click handleShowSingleThread
      prevHtml = $showComments.html()
      $showComments.html prevHtml.replace "Hide", "Show"

    handleShowSingleThread = ->
      $threadTitle = $local(".thread-title")
      $showComments = $local(".discussion-show-comments")

      rebindHideEvents = ->
        $threadTitle.unbind('click').click handleHideSingleThread
        $showComments.unbind('click').click handleHideSingleThread
        prevHtml = $showComments.html()
        $showComments.html prevHtml.replace "Show", "Hide"

      if $content.children(".comments").length
        $content.children(".comments").show()
        rebindHideEvents()
      else
        discussion_id = $threadTitle.parents(".discussion").attr("_id")
        url = Discussion.urlFor('retrieve_single_thread', discussion_id, id)
        Discussion.safeAjax
          $elem: $.merge($threadTitle, $showComments)
          url: url
          type: "GET"
          success: (response, textStatus) ->
            if not $$annotated_content_info?
              window.$$annotated_content_info = {}
            window.$$annotated_content_info = $.extend $$annotated_content_info, response['annotated_content_info']
            $content.append(response['html'])
            $content.find(".comment").each (index, comment) ->
              Discussion.initializeContent(comment)
              Discussion.bindContentEvents(comment)
            rebindHideEvents()
          dataType: 'json'
      
      
    $local(".thread-title").click handleShowSingleThread

    $local(".discussion-show-comments").click handleShowSingleThread

    $local(".discussion-reply-thread").click ->
      handleShowSingleThread($local(".thread-title"))
      handleReply(this)

    $local(".discussion-reply-comment").click ->
      handleReply(this)

    $local(".discussion-cancel-reply").click ->
      handleCancelReply(this)

    $local(".discussion-vote-up").click ->
      handleVote(this, "up")

    $local(".discussion-vote-down").click ->
      handleVote(this, "down")

    $local(".discussion-endorse").click ->
      handleEndorse(this)

    $local(".discussion-edit").click ->
      if $content.hasClass("thread")
        handleEditThread(this)
      else
        handleEditComment(this)

  initializeContent: (content) ->
    $content = $(content)
    $local = Discussion.generateLocal($content.children(".discussion-content"))
    $contentBody = $local(".content-body")
    raw_text = $contentBody.html()
    converter = Markdown.getMathCompatibleConverter()
    $contentBody.html(converter.makeHtml(raw_text))
    MathJax.Hub.Queue ["Typeset", MathJax.Hub, $contentBody.attr("id")]
    id = $content.attr("_id")
    if $$annotated_content_info?
      if not ($$annotated_content_info[id] || [])['editable']
        $local(".discussion-edit").remove()
