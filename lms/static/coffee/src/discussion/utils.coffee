if not @Discussion?
  @Discussion = {}

Discussion = @Discussion

@Discussion = $.extend @Discussion,

  generateLocal: (elem) ->
    (selector) -> $(elem).find(selector)

  generateDiscussionLink: (cls, txt, handler) ->
    $("<a>").addClass("discussion-link").
             attr("href", "javascript:void(0)").
             addClass(cls).html(txt).
             click(-> handler(this))

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
