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
      follow_thread           : "/courses/#{$$course_id}/discussion/threads/#{param}/follow"
      unfollow_thread         : "/courses/#{$$course_id}/discussion/threads/#{param}/unfollow"
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
    if type == "thread"
      id in $$user_info.subscribed_thread_ids
    else if type == "commentable" or type == "discussion"
      id in $$user_info.subscribed_commentable_ids
    else
      id in $$user_info.subscribed_user_ids

  formErrorHandler: (errorsField, success) ->
    (response, textStatus, xhr) ->
      if response.errors? and response.errors.length > 0
        errorsField.empty()
        for error in response.errors
          errorsField.append($("<li>").addClass("new-post-form-error").html(error))
      else
        success(response, textStatus, xhr)

  makeWmdEditor: ($content, $local, cls_identifier) ->
    elem = $local(".#{cls_identifier}")
    id = $content.attr("_id")
    appended_id = "-#{cls_identifier}-#{id}"
    imageUploadUrl = Discussion.urlFor('upload')
    editor = Markdown.makeWmdEditor elem, appended_id, imageUploadUrl
    wmdEditors["#{cls_identifier}-#{id}"] = editor
    console.log wmdEditors
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
    console.log wmdEditors
    console.log "#{cls_identifier}-#{id}"
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
