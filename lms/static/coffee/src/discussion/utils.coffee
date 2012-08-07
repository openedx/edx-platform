if not @Discussion?
  @Discussion = {}

Discussion = @Discussion

wmdEditors = {}

@Discussion = $.extend @Discussion,

  generateLocal: (elem) ->
    (selector) -> $(elem).find(selector)

  generateDiscussionLink: (cls, txt, handler) ->
    $("<a>").addClass("discussion-link")
            .attr("href", "javascript:void(0)")
            .addClass(cls).html(txt)
            .click -> handler(this)
    
  urlFor: (name, param, param1) ->
    {
      follow_discussion      : "/courses/#{$$course_id}/discussion/#{param}/follow"
      unfollow_discussion    : "/courses/#{$$course_id}/discussion/#{param}/unfollow"
      create_thread          : "/courses/#{$$course_id}/discussion/#{param}/threads/create"
      update_thread          : "/courses/#{$$course_id}/discussion/threads/#{param}/update"
      create_comment         : "/courses/#{$$course_id}/discussion/threads/#{param}/reply"
      delete_thread          : "/courses/#{$$course_id}/discussion/threads/#{param}/delete"
      upvote_thread          : "/courses/#{$$course_id}/discussion/threads/#{param}/upvote"
      downvote_thread        : "/courses/#{$$course_id}/discussion/threads/#{param}/downvote"
      undo_vote_for_thread   : "/courses/#{$$course_id}/discussion/threads/#{param}/unvote"
      follow_thread          : "/courses/#{$$course_id}/discussion/threads/#{param}/follow"
      unfollow_thread        : "/courses/#{$$course_id}/discussion/threads/#{param}/unfollow"
      update_comment         : "/courses/#{$$course_id}/discussion/comments/#{param}/update"
      endorse_comment        : "/courses/#{$$course_id}/discussion/comments/#{param}/endorse"
      create_sub_comment     : "/courses/#{$$course_id}/discussion/comments/#{param}/reply"
      delete_comment         : "/courses/#{$$course_id}/discussion/comments/#{param}/delete"
      upvote_comment         : "/courses/#{$$course_id}/discussion/comments/#{param}/upvote"
      downvote_comment       : "/courses/#{$$course_id}/discussion/comments/#{param}/downvote"
      undo_vote_for_comment  : "/courses/#{$$course_id}/discussion/comments/#{param}/unvote"
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

  bindLocalEvents: ($local, eventsHandler) ->
    for eventSelector, handler of eventsHandler
      [event, selector] = eventSelector.split(' ')
      $local(selector)[event] handler

  tagsInputOptions: ->
    autocomplete_url: Discussion.urlFor('tags_autocomplete')
    autocomplete:
      remoteDataType: 'json'
    interactive: true
    defaultText: "Tag your post: press enter after each tag"
    height: "30px"
    width: "100%"
    removeWithBackspace: true

  isSubscribed: (id, type) ->
    $$user_info? and (
      if type == "thread"
        id in $$user_info.subscribed_thread_ids
      else if type == "commentable" or type == "discussion"
        id in $$user_info.subscribed_commentable_ids
      else
        id in $$user_info.subscribed_user_ids
    )

  isUpvoted: (id) ->
    $$user_info? and (id in $$user_info.upvoted_ids)

  isDownvoted: (id) ->
    $$user_info? and (id in $$user_info.downvoted_ids)

  formErrorHandler: (errorsField, success) ->
    (response, textStatus, xhr) ->
      if response.errors? and response.errors.length > 0
        errorsField.empty()
        for error in response.errors
          errorsField.append($("<li>").addClass("new-post-form-error").html(error))
      else
        success(response, textStatus, xhr)

  postMathJaxProcessor: (text) ->
    RE_INLINEMATH = /^\$([^\$]*)\$/g
    RE_DISPLAYMATH = /^\$\$([^\$]*)\$\$/g
    Discussion.processEachMathAndCode text, (s, type) ->
      if type == 'display'
        s.replace RE_DISPLAYMATH, ($0, $1) ->
          "\\[" + $1 + "\\]"
      else if type == 'inline'
        s.replace RE_INLINEMATH, ($0, $1) ->
          "\\(" + $1 + "\\)"
      else
        s

  makeWmdEditor: ($content, $local, cls_identifier) ->
    elem = $local(".#{cls_identifier}")
    id = $content.attr("_id")
    appended_id = "-#{cls_identifier}-#{id}"
    imageUploadUrl = Discussion.urlFor('upload')
    editor = Markdown.makeWmdEditor elem, appended_id, imageUploadUrl, Discussion.postMathJaxProcessor
    wmdEditors["#{cls_identifier}-#{id}"] = editor
    editor

  getWmdEditor: ($content, $local, cls_identifier) ->
    id = $content.attr("_id")
    wmdEditors["#{cls_identifier}-#{id}"]

  getWmdContent: ($content, $local, cls_identifier) ->
    id = $content.attr("_id")
    $local("#wmd-input-#{cls_identifier}-#{id}").val()

  setWmdContent: ($content, $local, cls_identifier, text) ->
    id = $content.attr("_id")
    $local("#wmd-input-#{cls_identifier}-#{id}").val(text)
    wmdEditors["#{cls_identifier}-#{id}"].refreshPreview()

  getContentInfo: (id, attr) ->
    if not window.$$annotated_content_info?
      window.$$annotated_content_info = {}
    (window.$$annotated_content_info[id] || {})[attr]

  setContentInfo: (id, attr, value) ->
    if not window.$$annotated_content_info?
      window.$$annotated_content_info = {}
    window.$$annotated_content_info[id] ||= {}
    window.$$annotated_content_info[id][attr] = value

  bulkExtendContentInfo: (newInfos) ->
    if not window.$$annotated_content_info?
      window.$$annotated_content_info = {}
    window.$$annotated_content_info = $.extend window.$$annotated_content_info, newInfos

  subscriptionLink: (type, id) ->
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

    if Discussion.isSubscribed(id, type)
        unfollowLink()
    else
      followLink()
    
  processEachMathAndCode: (text, processor) ->
  
    codeArchive = []

    RE_DISPLAYMATH = /^([^\$]*?)\$\$([^\$]+?)\$\$(.*)$/m
    RE_INLINEMATH = /^([^\$]*?)\$([^\$]+?)\$(.*)$/m

    ESCAPED_DOLLAR = '@@ESCAPED_D@@'
    ESCAPED_BACKSLASH = '@@ESCAPED_B@@'

    processedText = ""

    $div = $("<div>").html(text)

    $div.find("code").each (index, code) ->
      codeArchive.push $(code).html()
      $(code).html(codeArchive.length - 1)

    text = $div.html()
    text = text.replace /\\\$/g, ESCAPED_DOLLAR

    while true
      if RE_INLINEMATH.test(text)
        text = text.replace RE_INLINEMATH, ($0, $1, $2, $3) ->
          processedText += $1 + processor("$" + $2 + "$", 'inline')
          $3
      else if RE_DISPLAYMATH.test(text)
        text = text.replace RE_DISPLAYMATH, ($0, $1, $2, $3) ->
          processedText += $1 + processor("$$" + $2 + "$$", 'display')
          $3
      else
        processedText += text
        break

    text = processedText
    text = text.replace(new RegExp(ESCAPED_DOLLAR, 'g'), '\\$')

    text = text.replace /\\\\\\\\/g, ESCAPED_BACKSLASH
    text = text.replace /\\begin\{([a-z]*\*?)\}([\s\S]*?)\\end\{\1\}/img, ($0, $1, $2) ->
      processor("\\begin{#{$1}}" + $2 + "\\end{#{$1}}")
    text = text.replace(new RegExp(ESCAPED_BACKSLASH, 'g'), '\\\\\\\\')

    $div = $("<div>").html(text)
    cnt = 0
    $div.find("code").each (index, code) ->
      $(code).html(processor(codeArchive[cnt], 'code'))
      cnt += 1

    text = $div.html()

    text
