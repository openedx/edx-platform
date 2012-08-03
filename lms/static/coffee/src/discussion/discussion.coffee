if not @Discussion?
  @Discussion = {}

Discussion = @Discussion

initializeVote = (index, content) ->
    $content = $(content)
    $local = Discussion.generateLocal($content.children(".discussion-content"))
    id = $content.attr("_id")
    if id in $$user_info.upvoted_ids
      $local(".discussion-vote-up").addClass("voted")
    else if id in $$user_info.downvoted_ids
      $local(".discussion-vote-down").addClass("voted")

subscriptionLink = (type, id) ->

  followLink = ->
    Discussion.generateDiscussionLink("discussion-follow-#{type}", "Follow", handleFollow)

  unfollowLink = ->
    Discussion.generateDiscussionLink("discussion-unfollow-#{type}", "Unfollow", handleUnfollow)

  handleFollow = (elem) ->
    Discussion.safeAjax
      $elem: $(elem)
      url: Discussion.urlFor("follow_#{type}", id)
      type: "POST"
      success: (response, textStatus) ->
        if textStatus == "success"
          $(elem).replaceWith unfollowLink()
      dataType: 'json'

  handleUnfollow = (elem) ->
    Discussion.safeAjax
      $elem: $(elem)
      url: Discussion.urlFor("unfollow_#{type}", id)
      type: "POST"
      success: (response, textStatus) ->
        if textStatus == "success"
          $(elem).replaceWith followLink()
      dataType: 'json'

  if type == 'discussion' and id in $$user_info.subscribed_commentable_ids \
    or type == 'thread' and id in $$user_info.subscribed_thread_ids
      unfollowLink()
  else
    followLink()

initializeFollowDiscussion = (discussion) ->
  $discussion = $(discussion)
  id = $following.attr("_id")
  $local = Discussion.generateLocal()
  $discussion.children(".discussion-non-content")
             .find(".discussion-title-wrapper")
             .append(subscriptionLink('discussion', id))

initializeFollowThread = (index, thread) ->
  $thread = $(thread)
  id = $thread.attr("_id")
  $thread.children(".discussion-content")
         .find(".follow-wrapper")
         .append(subscriptionLink('thread', id))

@Discussion = $.extend @Discussion,

  initializeDiscussion: (discussion) ->

    $local = Discussion.generateLocal(discussion)

    if $$user_info?
      $local(".comment").each(initializeVote)
      $local(".thread").each(initializeVote).each(initializeFollowThread)
      #initializeFollowDiscussion(discussion) TODO move this somewhere else

    $local(".new-post-tags").tagsInput Discussion.tagsInputOptions()

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
        view = { discussion_id: id }
        $discussionNonContent.append Mustache.render Discussion.newPostTemplate, view
        newPostBody = $(discussion).find(".new-post-body")
        if newPostBody.length
          Markdown.makeWmdEditor newPostBody, "-new-post-body-#{$(discussion).attr('_id')}", Discussion.urlFor('upload')

        $local(".new-post-tags").tagsInput Discussion.tagsInputOptions()

        $local(".discussion-submit-post").click ->
          handleSubmitNewPost(this)
        $local(".discussion-cancel-post").click ->
          handleCancelNewPost(this)

        $(elem).hide()

    handleUpdateDiscussionContent = ($elem, $discussion, url) ->

    handleAjaxSearch = (elem) ->
      handle
      $elem = $(elem)
      $discussion = $elem.parents(".discussion")
      Discussion.safeAjax
        $elem: $elem
        url: $elem.attr("action")
        data:
          text: $local(".search-input").val()
        type: "GET"
        success: (data, textStatus) ->
          $data = $(data)
          $discussion.replaceWith($data)
          Discussion.initializeDiscussion($data)
          Discussion.bindDiscussionEvents($data)
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
    
    Discussion.bindLocalEvents $local,

      "submit .search-wrapper-forum>.discussion-search-form": (event) ->
        event.preventDefault()
        text = $local(".search-input").val()
        isSearchWithinBoard = $local(".discussion-search-within-board").is(":checked")
        handleSearch(text, isSearchWithinBoard)

      "submit .search-wrapper-inline>.discussion-search-form": (event) ->
        event.preventDefault()
        handleAjaxSearch(this)

      "click .discussion-new-post": ->
        handleNewPost(this)

      "click .discussion-search-link": ->
        handleAjaxSearch(this)

      "click .discussion-inline-sort-link": ->
        handleAjaxSort(this)

    $discussion.find(".thread").each (index, thread) ->
      Discussion.initializeContent(thread)
      Discussion.bindContentEvents(thread)

    $discussion.find(".comment").each (index, comment) ->
      Discussion.initializeContent(comment)
      Discussion.bindContentEvents(comment)
