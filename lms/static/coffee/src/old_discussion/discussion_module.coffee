if not @Discussion?
  @Discussion = {}

Discussion = @Discussion

@Discussion = $.extend @Discussion,
  initializeDiscussionModule: (elem) ->
    $discussionModule = $(elem)
    $local = Discussion.generateLocal($discussionModule)
    handleShowDiscussion = (elem) ->
      $elem = $(elem)
      if not $local("section.discussion").length
        discussion_id = $elem.attr("discussion_id")
        url = Discussion.urlFor 'retrieve_discussion', discussion_id
        Discussion.safeAjax
          $elem: $elem
          url: url
          type: "GET"
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
