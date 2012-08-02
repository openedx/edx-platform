$ ->

  if $('#accordion').length
    active = $('#accordion ul:has(li.active)').index('#accordion ul')
    $('#accordion').bind('accordionchange', @log).accordion
      active: if active >= 0 then active else 1
      header: 'h3'
      autoHeight: false
    $('#open_close_accordion a').click @toggle
    $('#accordion').show()

  $(".discussion-module").each (index, elem) ->
    Discussion.initializeDiscussionModule(elem)

  $("section.discussion").each (index, discussion) ->
    Discussion.initializeDiscussion(discussion)
    Discussion.bindDiscussionEvents(discussion)

generateLocal = (elem) ->
  (selector) -> $(elem).find(selector)

generateDiscussionLink = (cls, txt, handler) ->
  $("<a>").addClass("discussion-link").
           attr("href", "javascript:void(0)").
           addClass(cls).html(txt).
           click(-> handler(this))

Discussion =

  newPostTemplate: """
    <form class="new-post-form" _id="{{discussion_id}}">
      <ul class="discussion-errors"></ul>    
      <input type="text" class="new-post-title title-input" placeholder="Title"/>
      <div class="new-post-body body-input"></div>
      <input class="new-post-tags" placeholder="Tags"/>
      <div class = "new-post-control">
        <a class="discussion-cancel-post" href="javascript:void(0)">Cancel</a>
        <a class="discussion-submit-post control-button" href="javascript:void(0)">Submit</a>
      </div>
    </form>
  """

  replyTemplate: """
    <form class="discussion-reply-new">
      <ul class="discussion-errors"></ul>
      <div class="reply-body"></div>
      <input type="checkbox" class="discussion-post-anonymously" id="discussion-post-anonymously-{{id}}" />
      <label for="discussion-post-anonymously-{{id}}">post anonymously</label>
      {{#showWatchCheckbox}}
      <input type="checkbox" class="discussion-auto-watch" id="discussion-autowatch-{{id}}" checked />
      <label for="discussion-auto-watch-{{id}}">follow this thread</label>
      {{/showWatchCheckbox}}
      <br />
      <div class = "reply-post-control">
        <a class="discussion-cancel-post" href="javascript:void(0)">Cancel</a>
        <a class="discussion-submit-post control-button" href="javascript:void(0)">Submit</a>
      </div>
    </form>
  """

  editThreadTemplate: """
    <form class="discussion-content-edit discussion-thread-edit" _id="{{id}}">
      <ul class="discussion-errors discussion-update-errors"></ul>    
      <input type="text" class="thread-title-edit title-input" placeholder="Title" value="{{title}}"/>
      <div class="thread-body-edit body-input">{{body}}</div>
      <input class="thread-tags-edit" placeholder="Tags" value="{{tags}}" />
      <div class = "edit-post-control">
        <a class="discussion-cancel-update" href="javascript:void(0)">Cancel</a>
        <a class="discussion-submit-update control-button" href="javascript:void(0)">Update</a>
      </div>
    </form>
  """

  editCommentTemplate: """
    <form class="discussion-content-edit discussion-comment-edit" _id="{{id}}">
      <ul class="discussion-errors discussion-update-errors"></ul>    
      <div class="comment-body-edit body-input">{{body}}</div>
      <a class="discussion-submit-update control-button" href="javascript:void(0)">Update</a>
      <a class="discussion-cancel-update control-button" href="javascript:void(0)">Cancel</a>
    </form>
  """

  urlFor: (name, param, param1) ->
    {
      watch_commentable      : "/courses/#{$$course_id}/discussion/#{param}/watch"
      unwatch_commentable    : "/courses/#{$$course_id}/discussion/#{param}/unwatch"
      create_thread          : "/courses/#{$$course_id}/discussion/#{param}/threads/create"
      update_thread          : "/courses/#{$$course_id}/discussion/threads/#{param}/update"
      create_comment         : "/courses/#{$$course_id}/discussion/threads/#{param}/reply"
      delete_thread          : "/courses/#{$$course_id}/discussion/threads/#{param}/delete"
      upvote_thread          : "/courses/#{$$course_id}/discussion/threads/#{param}/upvote"
      downvote_thread        : "/courses/#{$$course_id}/discussion/threads/#{param}/downvote"
      watch_thread           : "/courses/#{$$course_id}/discussion/threads/#{param}/watch"
      unwatch_thread         : "/courses/#{$$course_id}/discussion/threads/#{param}/unwatch"
      update_comment         : "/courses/#{$$course_id}/discussion/comments/#{param}/update"
      endorse_comment        : "/courses/#{$$course_id}/discussion/comments/#{param}/endorse"
      create_sub_comment     : "/courses/#{$$course_id}/discussion/comments/#{param}/reply"
      delete_comment         : "/courses/#{$$course_id}/discussion/comments/#{param}/delete"
      upvote_comment         : "/courses/#{$$course_id}/discussion/comments/#{param}/upvote"
      downvote_comment       : "/courses/#{$$course_id}/discussion/comments/#{param}/downvote"
      upload                 : "/courses/#{$$course_id}/discussion/upload"
      search                 : "/courses/#{$$course_id}/discussion/forum/search"
      tags_autocomplete      : "/courses/#{$$course_id}/discussion/threads/tags/autocomplete"
      retrieve_discussion    : "/courses/#{$$course_id}/discussion/forum/#{param}/inline"
      retrieve_single_thread : "/courses/#{$$course_id}/discussion/forum/#{param}/threads/#{param1}"
    }[name]

  safeAjax: (params) ->
    $elem = params.$elem
    if $elem.attr("disabled")
      return
    $elem.attr("disabled", "disabled")
    $.ajax(params).always ->
      $elem.removeAttr("disabled")

  handleAnchorAndReload: (response) ->
    #window.location = window.location.pathname + "#" + response['id']
    window.location.reload()

  initializeDiscussionModule: (elem) ->
    $discussionModule = $(elem)
    $local = generateLocal($discussionModule)
    handleShowDiscussion = (elem) ->
      $elem = $(elem)
      if not $local("section.discussion").length
        discussion_id = $elem.attr("discussion_id")
        url = Discussion.urlFor 'retrieve_discussion', discussion_id
        Discussion.safeAjax
          $elem: $elem
          url: url
          method: "GET"
          success: (data, textStatus, xhr) ->
            $discussionModule.append(data)
            discussion = $local("section.discussion")
            Discussion.initializeDiscussion(discussion)
            Discussion.bindDiscussionEvents(discussion)
            $elem.html("Hide Discussion")
            $elem.unbind('click').click ->
              handleHideDiscussion(this)
          dataType: 'html'
      else
        $local("section.discussion").show()
        $elem.html("Hide Discussion")
        $elem.unbind('click').click ->
          handleHideDiscussion(this)

    handleHideDiscussion = (elem) ->
      $local("section.discussion").hide()
      $elem = $(elem)
      $elem.html("Show Discussion")
      $elem.unbind('click').click ->
        handleShowDiscussion(this)

    $local(".discussion-show").click ->
      handleShowDiscussion(this)

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
        unwatchThread = generateDiscussionLink("discussion-unwatch-thread", "Unfollow", handleUnwatchThread)
        $local(".info").append(unwatchThread)
      else
        watchThread = generateDiscussionLink("discussion-watch-thread", "Follow", handleWatchThread)
        $local(".info").append(watchThread)

    $local = generateLocal(discussion)

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

  bindContentEvents: (content) ->

    $content = $(content)
    $discussionContent = $content.children(".discussion-content")
    $local = generateLocal($discussionContent)

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
        $local(".discussion-submit-post").click handleSubmitReply
        $local(".discussion-cancel-post").click handleCancelReply
      $local(".discussion-link").hide()
      $discussionContent.attr("status", "reply")

    handleCancelReply = (elem) ->
      $replyView = $local(".discussion-reply-new")
      if $replyView.length
        $replyView.hide()
      reply = generateDiscussionLink("discussion-reply", "Reply", handleReply)
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
          method: "GET"
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
    $local = generateLocal($content.children(".discussion-content"))
    $contentBody = $local(".content-body")
    raw_text = $contentBody.html()
    converter = Markdown.getMathCompatibleConverter()
    $contentBody.html(converter.makeHtml(raw_text))
    MathJax.Hub.Queue ["Typeset", MathJax.Hub, $contentBody.attr("id")]
    id = $content.attr("_id")
    if $$annotated_content_info?
      if not ($$annotated_content_info[id] || [])['editable']
        $local(".discussion-edit").remove()

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
      console.log $(elem).attr("action")
      $elem = $(elem)
      $discussionModule = $elem.parents(".discussion-module")
      $discussion = $discussionModule.find(".discussion")
      Discussion.safeAjax
        $elem: $elem
        url: $elem.attr("action")
        data:
          text: $local(".search-input").val()
        method: "GET"
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
        method: "GET"
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
