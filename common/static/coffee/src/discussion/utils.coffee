class @DiscussionUtil

  @wmdEditors: {}

  @getTemplate: (id) ->
    $("script##{id}").html()

  @setUser: (user) ->
    @user = user

  @getUser: () ->
    @user

  @loadRoles: (roles)->
    @roleIds = roles

  @loadRolesFromContainer: ->
    @loadRoles($("#discussion-container").data("roles"))

  @isStaff: (user_id) ->
    user_id ?= @user?.id
    staff = _.union(@roleIds['Moderator'], @roleIds['Administrator'])
    _.include(staff, parseInt(user_id))

  @isTA: (user_id) ->
    user_id ?= @user?.id
    ta = _.union(@roleIds['Community TA'])
    _.include(ta, parseInt(user_id))

  @isPrivilegedUser: (user_id) ->
    @isStaff(user_id) || @isTA(user_id)

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
      users                   : "/courses/#{$$course_id}/discussion/users"
      search                  : "/courses/#{$$course_id}/discussion/forum/search"
      retrieve_discussion     : "/courses/#{$$course_id}/discussion/forum/#{param}/inline"
      retrieve_single_thread  : "/courses/#{$$course_id}/discussion/forum/#{param}/threads/#{param1}"
      openclose_thread        : "/courses/#{$$course_id}/discussion/threads/#{param}/close"
      permanent_link_thread   : "/courses/#{$$course_id}/discussion/forum/#{param}/threads/#{param1}"
      permanent_link_comment  : "/courses/#{$$course_id}/discussion/forum/#{param}/threads/#{param1}##{param2}"
      user_profile            : "/courses/#{$$course_id}/discussion/forum/users/#{param}"
      followed_threads        : "/courses/#{$$course_id}/discussion/forum/users/#{param}/followed"
      threads                 : "/courses/#{$$course_id}/discussion/forum"
      "enable_notifications"  : "/notification_prefs/enable/"
      "disable_notifications" : "/notification_prefs/disable/"
      "notifications_status" : "/notification_prefs/status/"
    }[name]

  @ignoreEnterKey: (event) =>
    if event.which == 13
      event.preventDefault()

  @activateOnSpace: (event, func) ->
    if event.which == 32
      event.preventDefault()
      func(event)

  @makeFocusTrap: (elem) ->
    elem.keydown(
      (event) ->
        if event.which == 9 # Tab
          event.preventDefault()
    )

  @showLoadingIndicator: (element, takeFocus) ->
    @$_loading = $("<div class='loading-animation' tabindex='0'><span class='sr'>" + gettext("Loading content") + "</span></div>")
    element.after(@$_loading)
    if takeFocus
      @makeFocusTrap(@$_loading)
      @$_loading.focus()

  @hideLoadingIndicator: () ->
    @$_loading.remove()

  @discussionAlert: (header, body) ->
    if $("#discussion-alert").length == 0
      alertDiv = $("<div class='modal' role='alertdialog' id='discussion-alert' aria-describedby='discussion-alert-message'/>").css("display", "none")
      alertDiv.html(
        "<div class='inner-wrapper discussion-alert-wrapper'>" +
        "  <button class='close-modal dismiss' aria-hidden='true'><i class='icon fa fa-times'></i></button>" +
        "  <header><h2/><hr/></header>" +
        "  <p id='discussion-alert-message'/>" +
        "  <hr/>" +
        "  <button class='dismiss'>" + gettext("OK") + "</button>" +
        "</div>"
      )
      @makeFocusTrap(alertDiv.find("button"))
      alertTrigger = $("<a href='#discussion-alert' id='discussion-alert-trigger'/>").css("display", "none")
      alertTrigger.leanModal({closeButton: "#discussion-alert .dismiss", overlay: 1, top: 200})
      $("body").append(alertDiv).append(alertTrigger)
    $("#discussion-alert header h2").html(header)
    $("#discussion-alert p").html(body)
    $("#discussion-alert-trigger").click()
    $("#discussion-alert button").focus()

  @safeAjax: (params) ->
    $elem = params.$elem

    if $elem and $elem.attr("disabled")
      deferred = $.Deferred()
      deferred.reject()
      return deferred.promise()

    params["url"] = URI(params["url"]).addSearch ajax: 1
    params["beforeSend"] = =>
      if $elem
        $elem.attr("disabled", "disabled")
      if params["$loading"]
        if params["loadingCallback"]?
          params["loadingCallback"].apply(params["$loading"])
        else
          @showLoadingIndicator($(params["$loading"]), params["takeFocus"])
    if !params["error"]
      params["error"] = =>
        @discussionAlert(
          gettext("Sorry"),
          gettext("We had some trouble processing your request. Please ensure you have copied any unsaved work and then reload the page.")
        )
    request = $.ajax(params).always =>
      if $elem
        $elem.removeAttr("disabled")
      if params["$loading"]
        if params["loadedCallback"]?
          params["loadedCallback"].apply(params["$loading"])
        else
          @hideLoadingIndicator()
    return request

  @updateWithUndo: (model, updates, safeAjaxParams, errorMsg) ->
    if errorMsg
      safeAjaxParams.error = => @discussionAlert(gettext("Sorry"), errorMsg)
    undo = _.pick(model.attributes, _.keys(updates))
    model.set(updates)
    @safeAjax(safeAjaxParams).fail(() -> model.set(undo))

  @bindLocalEvents: ($local, eventsHandler) ->
    for eventSelector, handler of eventsHandler
      [event, selector] = eventSelector.split(' ')
      $local(selector).unbind(event)[event] handler

  @formErrorHandler: (errorsField) ->
    (xhr, textStatus, error) ->
      makeErrorElem = (message) ->
        $("<li>").addClass("post-error").html(message)
      errorsField.empty().show()
      if xhr.status == 400
        response = JSON.parse(xhr.responseText)
        if response.errors? and response.errors.length > 0
          for error in response.errors
            errorsField.append(makeErrorElem(error))
      else
        errorsField.append(
          makeErrorElem(
            gettext("We had some trouble processing your request. Please try again.")
          )
        )

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
      return text.substr(0, minLength) + gettext('…')

  @abbreviateHTML: (html, minLength) ->
    # Abbreviates the html to at least minLength characters, stopping at word boundaries
    truncated_text = jQuery.truncate(html, {length: minLength, noBreaks: true, ellipsis: gettext('…')})
    $result = $("<div>" + truncated_text + "</div>")
    imagesToReplace = $result.find("img:not(:first)")
    if imagesToReplace.length > 0
        $result.append("<p><em>Some images in this post have been omitted</em></p>")
    imagesToReplace.replaceWith("<em>image omitted</em>")
    $result.html()

  @getPaginationParams: (curPage, numPages, pageUrlFunc) =>
    delta = 2
    minPage = Math.max(curPage - delta, 1)
    maxPage = Math.min(curPage + delta, numPages)
    pageInfo = (pageNum) -> {number: pageNum, url: pageUrlFunc(pageNum)}
    params =
      page: curPage
      lowPages: _.range(minPage, curPage).map(pageInfo)
      highPages: _.range(curPage+1, maxPage+1).map(pageInfo)
      previous: if curPage > 1 then pageInfo(curPage - 1) else null
      next: if curPage < numPages then pageInfo(curPage + 1) else null
      leftdots: minPage > 2
      rightdots: maxPage < numPages-1
      first: if minPage > 1 then pageInfo(1) else null
      last: if maxPage < numPages then pageInfo(numPages) else null
