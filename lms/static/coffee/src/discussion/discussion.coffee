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
    $discussionNonContent = $discussion.children(".discussion-local")
    $local = Discussion.generateLocal($discussionNonContent)

    id = $discussion.attr("_id")

    handleSubmitNewPost = (elem) ->
      title = $local(".new-post-title").val()
      body = Discussion.getWmdContent $discussion, $local, "new-post-body"
      tags = $local(".new-post-tags").val()
      url = Discussion.urlFor('create_thread', id)
      Discussion.safeAjax
        $elem: $(elem)
        url: url
        type: "POST"
        dataType: 'json'
        data:
          title: title
          body: body
          tags: tags
        error: Discussion.formErrorHandler($local(".new-post-form-errors"))
        success: (response, textStatus) ->
          $thread = $(response.html)
          $discussion.children(".threads").prepend($thread)
          $local(".new-post-form").remove()

    handleCancelNewPost = (elem) ->
      if $discussion.hasClass("inline-discussion")
        $local(".new-post-form").addClass("collapsed")
      else
        $local(".new-post-form").hide()

    handleSimilarPost = (elem) ->
      $title = $local(".new-post-title")
      $wrapper = $local(".new-post-similar-posts-wrapper")
      $similarPosts = $local(".new-post-similar-posts")
      prevText = $title.attr("prev-text")
      text = $title.val()
      if text == prevText
        if $local(".similar-post").length
          $wrapper.show()
      else if $.trim(text).length
        Discussion.safeAjax
          $elem: $(elem)
          url: Discussion.urlFor 'search_similar_threads', id
          type: "GET"
          dateType: 'json'
          data:
            text: $local(".new-post-title").val()
          success: (response, textStatus) ->
            $similarPosts.empty()
            console.log response
            if $.type(response) == "array" and response.length
              $wrapper.show()
              for thread in response
                #singleThreadUrl = Discussion.urlFor 'retrieve_single_thread 
                $similarPost = $("<a>").addClass("similar-post")
                                       .html(thread["title"])
                                       .attr("href", "javascript:void(0)") #TODO
                                       .appendTo($similarPosts)
            else
              $wrapper.hide()
      else
        $wrapper.hide()
      $title.attr("prev-text", text)

    initializeNewPost = ->
      view = { discussion_id: id }
      $discussionNonContent = $discussion.children(".discussion-non-content")

      if not $local(".wmd-panel").length
        $discussionNonContent.append Mustache.render Discussion.newPostTemplate, view
        $newPostBody = $local(".new-post-body")
        Discussion.makeWmdEditor $discussion, $local, "new-post-body"

        $input = Discussion.getWmdInput($discussion, $local, "new-post-body")
        $input.attr("placeholder", "post a new topic...")
        if $discussion.hasClass("inline-discussion")
          $input.bind 'focus', (e) ->
            $local(".new-post-form").removeClass('collapsed')
        else
          $local(".new-post-form").removeClass('collapsed')

        $local(".new-post-tags").tagsInput Discussion.tagsInputOptions()

        $local(".new-post-title").blur ->
          handleSimilarPost(this)

        $local(".hide-similar-posts").click ->
          $local(".new-post-similar-posts-wrapper").hide()

        $local(".discussion-submit-post").click ->
          handleSubmitNewPost(this)
        $local(".discussion-cancel-post").click ->
          handleCancelNewPost(this)

      $local(".new-post-form").show()

    handleAjaxReloadDiscussion = (elem, url) ->
      if not url then return
      $elem = $(elem)
      $discussion = $elem.parents("section.discussion")
      Discussion.safeAjax
        $elem: $elem
        url: url
        type: "GET"
        dataType: 'html'
        success: (data, textStatus) ->
          $data = $(data)
          $discussion.replaceWith($data)
          $discussion = $(".discussion[_id='#{id}']")
          Discussion.initializeDiscussion($discussion)
          Discussion.bindDiscussionEvents($discussion)

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

    if $discussion.hasClass("inline-discussion")
      initializeNewPost()

    $discussionSidebar = $(".discussion-sidebar")
    if $discussionSidebar.length
      $sidebarLocal = Discussion.generateLocal($discussionSidebar)
      Discussion.bindLocalEvents $sidebarLocal,
        "click .sidebar-new-post-button": (event) ->
          initializeNewPost()

    Discussion.bindLocalEvents $local,

      "submit .search-wrapper>.discussion-search-form": (event) ->
        event.preventDefault()
        handleAjaxSearch(this)

      "click .discussion-search-link": ->
        handleAjaxSearch($local(".search-wrapper>.discussion-search-form"))

      "click .discussion-sort-link": ->
        handleAjaxSort(this)

    $discussion.children(".discussion-paginator").find(".discussion-page-link").unbind('click').click ->
      handleAjaxPage(this)
