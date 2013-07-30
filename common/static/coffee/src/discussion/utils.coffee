$ ->
  if !window.$$contents
    window.$$contents = {}
  $.fn.extend
    loading: ->
      @$_loading = $("<div class='loading-animation'></div>")
      $(this).after(@$_loading)
    loaded: ->
      @$_loading.remove()

class @DiscussionUtil

  @wmdEditors: {}

  @getTemplate: (id) ->
    $("script##{id}").html()

  @loadRoles: (roles)->
    @roleIds = roles

  @loadFlagModerator: (what)->
    @isFlagModerator = ((what=="True") or (what == 1))

  @loadRolesFromContainer: ->
    @loadRoles($("#discussion-container").data("roles"))
    @loadFlagModerator($("#discussion-container").data("flag-moderator"))

  @isStaff: (user_id) ->
    staff = _.union(@roleIds['Staff'], @roleIds['Moderator'], @roleIds['Administrator'])
    _.include(staff, parseInt(user_id))

  @isTA: (user_id) ->
    ta = _.union(@roleIds['Community TA'])
    _.include(ta, parseInt(user_id))

  @bulkUpdateContentInfo: (infos) ->
    for id, info of infos
      Content.getContent(id).updateInfo(info)

  @generateDiscussionLink: (cls, txt, handler) ->
    $("<a>").addClass("discussion-link")
            .attr("href", "javascript:void(0)")
            .addClass(cls).html(txt)
            .click -> handler(this)

  @urlFor: (name, param, param1, param2) ->
    {
      follow_discussion       : "/courses/#{$$course_id}/discussion/#{param}/follow"
      unfollow_discussion     : "/courses/#{$$course_id}/discussion/#{param}/unfollow"
      create_thread           : "/courses/#{$$course_id}/discussion/#{param}/threads/create"
      search_similar_threads  : "/courses/#{$$course_id}/discussion/#{param}/threads/search_similar"
      update_thread           : "/courses/#{$$course_id}/discussion/threads/#{param}/update"
      create_comment          : "/courses/#{$$course_id}/discussion/threads/#{param}/reply"
      delete_thread           : "/courses/#{$$course_id}/discussion/threads/#{param}/delete"
      flagAbuse_thread        : "/courses/#{$$course_id}/discussion/threads/#{param}/flagAbuse"
      unFlagAbuse_thread      : "/courses/#{$$course_id}/discussion/threads/#{param}/unFlagAbuse"
      flagAbuse_comment       : "/courses/#{$$course_id}/discussion/comments/#{param}/flagAbuse"
      unFlagAbuse_comment     : "/courses/#{$$course_id}/discussion/comments/#{param}/unFlagAbuse"
      upvote_thread           : "/courses/#{$$course_id}/discussion/threads/#{param}/upvote"
      downvote_thread         : "/courses/#{$$course_id}/discussion/threads/#{param}/downvote"
      pin_thread              : "/courses/#{$$course_id}/discussion/threads/#{param}/pin"
      un_pin_thread           : "/courses/#{$$course_id}/discussion/threads/#{param}/unpin"
      undo_vote_for_thread    : "/courses/#{$$course_id}/discussion/threads/#{param}/unvote"
      follow_thread           : "/courses/#{$$course_id}/discussion/threads/#{param}/follow"
      unfollow_thread         : "/courses/#{$$course_id}/discussion/threads/#{param}/unfollow"
      update_comment          : "/courses/#{$$course_id}/discussion/comments/#{param}/update"
      endorse_comment         : "/courses/#{$$course_id}/discussion/comments/#{param}/endorse"
      create_sub_comment      : "/courses/#{$$course_id}/discussion/comments/#{param}/reply"
      delete_comment          : "/courses/#{$$course_id}/discussion/comments/#{param}/delete"
      upvote_comment          : "/courses/#{$$course_id}/discussion/comments/#{param}/upvote"
      downvote_comment        : "/courses/#{$$course_id}/discussion/comments/#{param}/downvote"
      undo_vote_for_comment   : "/courses/#{$$course_id}/discussion/comments/#{param}/unvote"
      upload                  : "/courses/#{$$course_id}/discussion/upload"
      search                  : "/courses/#{$$course_id}/discussion/forum/search"
      tags_autocomplete       : "/courses/#{$$course_id}/discussion/threads/tags/autocomplete"
      retrieve_discussion     : "/courses/#{$$course_id}/discussion/forum/#{param}/inline"
      retrieve_single_thread  : "/courses/#{$$course_id}/discussion/forum/#{param}/threads/#{param1}"
      update_moderator_status : "/courses/#{$$course_id}/discussion/users/#{param}/update_moderator_status"
      openclose_thread        : "/courses/#{$$course_id}/discussion/threads/#{param}/close"
      permanent_link_thread   : "/courses/#{$$course_id}/discussion/forum/#{param}/threads/#{param1}"
      permanent_link_comment  : "/courses/#{$$course_id}/discussion/forum/#{param}/threads/#{param1}##{param2}"
      user_profile            : "/courses/#{$$course_id}/discussion/forum/users/#{param}"
      followed_threads        : "/courses/#{$$course_id}/discussion/forum/users/#{param}/followed"
      threads                 : "/courses/#{$$course_id}/discussion/forum"
      "enable_notifications"  : "/notification_prefs/enable/"
      "disable_notifications" : "/notification_prefs/disable/"
      "notifications_status" : "/notification_prefs/status"
    }[name]

  @safeAjax: (params) ->
    $elem = params.$elem
    if $elem and $elem.attr("disabled")
      return
    params["url"] = URI(params["url"]).addSearch ajax: 1
    params["beforeSend"] = ->
      if $elem
        $elem.attr("disabled", "disabled")
      if params["$loading"]
        if params["loadingCallback"]?
          params["loadingCallback"].apply(params["$loading"])
        else
          params["$loading"].loading()
    request = $.ajax(params).always ->
      if $elem
        $elem.removeAttr("disabled")
      if params["$loading"]
        if params["loadedCallback"]?
          params["loadedCallback"].apply(params["$loading"])
        else
          params["$loading"].loaded()
    return request

  @get: ($elem, url, data, success) ->
    @safeAjax
      $elem: $elem
      url: url
      type: "GET"
      dataType: "json"
      data: data
      success: success

  @post: ($elem, url, data, success) ->
    @safeAjax
      $elem: $elem
      url: url
      type: "POST"
      dataType: "json"
      data: data
      success: success

  @bindLocalEvents: ($local, eventsHandler) ->
    for eventSelector, handler of eventsHandler
      [event, selector] = eventSelector.split(' ')
      $local(selector).unbind(event)[event] handler

  @processTag: (text) ->
    text.toLowerCase()

  @tagsInputOptions: ->
    autocomplete_url: @urlFor('tags_autocomplete')
    autocomplete:
      remoteDataType: 'json'
    interactive: true
    height: '30px'
    width: '100%'
    defaultText: "Tag your post: press enter after each tag"
    removeWithBackspace: true
    preprocessTag: @processTag

  @formErrorHandler: (errorsField) ->
    (xhr, textStatus, error) ->
      response = JSON.parse(xhr.responseText)
      if response.errors? and response.errors.length > 0
        errorsField.empty()
        for error in response.errors
          errorsField.append($("<li>").addClass("new-post-form-error").html(error)).show()

  @clearFormErrors: (errorsField) ->
    errorsField.empty()

  @postMathJaxProcessor: (text) ->
    RE_INLINEMATH = /^\$([^\$]*)\$/g
    RE_DISPLAYMATH = /^\$\$([^\$]*)\$\$/g
    @processEachMathAndCode text, (s, type) ->
      if type == 'display'
        s.replace RE_DISPLAYMATH, ($0, $1) ->
          "\\[" + $1 + "\\]"
      else if type == 'inline'
        s.replace RE_INLINEMATH, ($0, $1) ->
          "\\(" + $1 + "\\)"
      else
        s

  @makeWmdEditor: ($content, $local, cls_identifier) ->
    elem = $local(".#{cls_identifier}")
    placeholder = elem.data('placeholder')
    id = elem.attr("data-id") # use attr instead of data because we want to avoid type coercion
    appended_id = "-#{cls_identifier}-#{id}"
    imageUploadUrl = @urlFor('upload')
    _processor = (_this) ->
      (text) -> _this.postMathJaxProcessor(text)
    editor = Markdown.makeWmdEditor elem, appended_id, imageUploadUrl, _processor(@)
    @wmdEditors["#{cls_identifier}-#{id}"] = editor
    if placeholder?
      elem.find("#wmd-input#{appended_id}").attr('placeholder', placeholder)
    editor

  @getWmdEditor: ($content, $local, cls_identifier) ->
    elem = $local(".#{cls_identifier}")
    id = elem.attr("data-id") # use attr instead of data because we want to avoid type coercion
    @wmdEditors["#{cls_identifier}-#{id}"]

  @getWmdInput: ($content, $local, cls_identifier) ->
    elem = $local(".#{cls_identifier}")
    id = elem.attr("data-id") # use attr instead of data because we want to avoid type coercion
    $local("#wmd-input-#{cls_identifier}-#{id}")

  @getWmdContent: ($content, $local, cls_identifier) ->
    @getWmdInput($content, $local, cls_identifier).val()

  @setWmdContent: ($content, $local, cls_identifier, text) ->
    @getWmdInput($content, $local, cls_identifier).val(text)
    @getWmdEditor($content, $local, cls_identifier).refreshPreview()

  @subscriptionLink: (type, id) ->
    followLink = ->
      @generateDiscussionLink("discussion-follow-#{type}", "Follow", handleFollow)

    unfollowLink = ->
      @generateDiscussionLink("discussion-unfollow-#{type}", "Unfollow", handleUnfollow)

    handleFollow = (elem) ->
      @safeAjax
        $elem: $(elem)
        url: @urlFor("follow_#{type}", id)
        type: "POST"
        success: (response, textStatus) ->
          if textStatus == "success"
            $(elem).replaceWith unfollowLink()
        dataType: 'json'

    handleUnfollow = (elem) ->
      @safeAjax
        $elem: $(elem)
        url: @urlFor("unfollow_#{type}", id)
        type: "POST"
        success: (response, textStatus) ->
          if textStatus == "success"
            $(elem).replaceWith followLink()
        dataType: 'json'

    if @isSubscribed(id, type)
        unfollowLink()
    else
      followLink()

  @processEachMathAndCode: (text, processor) ->

    codeArchive = []

    RE_DISPLAYMATH = /^([^\$]*?)\$\$([^\$]*?)\$\$(.*)$/m
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
          #processedText += $1 + processor("$$" + $2 + "$$", 'display')
          #bug fix, ordering is off
          processedText =  processor("$$" + $2 + "$$", 'display') + processedText
          processedText = $1 + processedText
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

  @unescapeHighlightTag: (text) ->
    text.replace(/\&lt\;highlight\&gt\;/g, "<span class='search-highlight'>")
        .replace(/\&lt\;\/highlight\&gt\;/g, "</span>")

  @stripHighlight: (text) ->
    text.replace(/\&(amp\;)?lt\;highlight\&(amp\;)?gt\;/g, "")
        .replace(/\&(amp\;)?lt\;\/highlight\&(amp\;)?gt\;/g, "")

  @stripLatexHighlight: (text) ->
    @processEachMathAndCode text, @stripHighlight

  @markdownWithHighlight: (text) ->
    text = text.replace(/^\&gt\;/gm, ">")
    converter = Markdown.getMathCompatibleConverter()
    text = @unescapeHighlightTag @stripLatexHighlight converter.makeHtml text
    return text.replace(/^>/gm,"&gt;")

  @abbreviateString: (text, minLength) ->
    # Abbreviates a string to at least minLength characters, stopping at word boundaries
    if text.length<minLength
      return text
    else
      while minLength < text.length && text[minLength] != ' '
        minLength++
      return text.substr(0, minLength) + '...'

