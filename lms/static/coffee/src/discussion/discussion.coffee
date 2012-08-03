if not @Discussion?
  @Discussion = {}

Discussion = @Discussion

initializeFollowDiscussion = (discussion) ->
  $discussion = $(discussion)
  id = $following.attr("_id")
  $local = Discussion.generateLocal()
  $discussion.children(".discussion-non-content")
             .find(".discussion-title-wrapper")
             .append(Discussion.subscriptionLink('discussion', id))

@Discussion = $.extend @Discussion,

  initializeDiscussion: (discussion) ->
    $discussion = $(discussion)
    $discussion.find(".thread").each (index, thread) ->
      Discussion.initializeContent(thread)
      Discussion.bindContentEvents(thread)
    $discussion.find(".comment").each (index, comment) ->
      Discussion.initializeContent(comment)
      Discussion.bindContentEvents(comment)

    #initializeFollowDiscussion(discussion) TODO move this somewhere else

  bindDiscussionEvents: (discussion) ->

    $discussion = $(discussion)
    $discussionNonContent = $discussion.children(".discussion-non-content")
    $local = Discussion.generateLocal($discussionNonContent)

    id = $discussion.attr("_id")

    handleSearch = (text, isSearchWithinBoard) ->
      if text.length
        if $local(".discussion-search-within-board").is(":checked")
          window.location = window.location.pathname + '?text=' + encodeURI(text)
        else
          window.location = Discussion.urlFor('search') + '?text=' + encodeURI(text)

    handleSubmitNewPost = (elem) ->
      title = $local(".new-post-title").val()
      body = Discussion.getWmdContent $discussion, $local, "new-post-body"
      tags = $local(".new-post-tags").val()
      url = Discussion.urlFor('create_thread', $local(".new-post-form").attr("_id"))
      Discussion.safeAjax
        $elem: $(elem)
        url: url
        type: "POST"
        dataType: 'json'
        data:
          title: title
          body: body
          tags: tags
        success: Discussion.formErrorHandler($local(".new-post-form-error"), (response, textStatus) ->
          $thread = $(response.html)
          $discussion.children(".threads").prepend($thread)
          Discussion.setWmdContent $discussion, $local, "new-post-body", ""
          Discussion.setContentInfo response.content['id'], 'editable', true
          Discussion.initializeContent($thread)
          Discussion.bindContentEvents($thread)
          $(".new-post-form").hide()
          $local(".discussion-new-post").show()
        )

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
        newPostBody = $discussion.find(".new-post-body")
        if newPostBody.length
          Discussion.makeWmdEditor $discussion, $local, "new-post-body"

        $local(".new-post-tags").tagsInput Discussion.tagsInputOptions()

        $local(".discussion-submit-post").click ->
          handleSubmitNewPost(this)
        $local(".discussion-cancel-post").click ->
          handleCancelNewPost(this)

        $(elem).hide()

    handleAjaxReloadDiscussion = (elem, url) ->
      $elem = $(elem)
      $discussion = $elem.parents(".discussion")
      console.log url
      console.log $elem
      Discussion.safeAjax
        $elem: $elem
        url: url
        type: "GET"
        dataType: 'html'
        success: (data, textStatus) ->
          $data = $(data)
          $discussion.replaceWith($data)
          Discussion.initializeDiscussion($data)
          Discussion.bindDiscussionEvents($data)

    handleAjaxSearch = (elem) ->
      $elem = $(elem)
      url = URI($elem.attr("action")).addSearch({text: $local(".search-input").val()})
      handleAjaxReloadDiscussion($elem, url)

    handleAjaxSort = (elem) ->
      $elem = $(elem)
      url = $elem.attr("sort-url")
      handleAjaxReloadDiscussion($elem, url)

    handleAjaxPage = (elem) ->
      $elem = $(elem)
      url = $elem.attr("page-url")
      handleAjaxReloadDiscussion($elem, url)
    
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

    $discussion.children(".discussion-paginator").find(".discussion-inline-page-link").click ->
      handleAjaxPage(this)
