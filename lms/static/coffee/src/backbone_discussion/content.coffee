class @Content extends Backbone.Model

  template: -> DiscussionUtil.getTemplate('_content')

  actions:
    editable: '.admin-edit'
    can_reply: '.discussion-reply'
    can_endorse: '.admin-endorse'
    can_delete: '.admin-delete'
    can_openclose: '.admin-openclose'
    
  isUpvoted: ->
    DiscussionUtil.isUpvoted @id

  isDownvoted: ->
    DiscussionUtil.isDownvoted @id

  can: (action) ->
    DiscussionUtil.getContentInfo @id, action

  initialize: ->
    @set('comments', new Comments())
    if @get('children')
      @get('comments').reset @get('children'), {silent: false}

class @ContentView extends Backbone.View

  $: (selector) ->
    @$local.find(selector)

  showSingleThread: (event) ->
    $threadTitle = @$(".thread-title")
    $showComments = @$(".discussion-show-comments")

    if not $showComments.hasClass("first-time") and (not $showComments.length or not $threadTitle.length)
      return

    rebindHideEvents = ->
      $threadTitle.unbind('click').click @hideSingleThread
      $showComments.unbind('click').click @hideSingleThread
      $showComments.removeClass("discussion-show-comments")
                   .addClass("discussion-hide-comments")
      prevHtml = $showComments.html()
      $showComments.html prevHtml.replace "Show", "Hide"

    if not $showComments.hasClass("first-time") and @$el.children(".comments").length
      @$el.children(".comments").show()
      rebindHideEvents()
    else
      discussion_id = @model.discussion.id
      url = DiscussionUtil.urlFor('retrieve_single_thread', discussion_id, @model.id)
      DiscussionUtil.safeAjax
        $elem: $.merge($threadTitle, $showComments)
        url: url
        type: "GET"
        dataType: 'json'
        success: (response, textStatus) =>
          DiscussionUtil.bulkExtendContentInfo response['annotated_content_info']
          @$el.append(response['html'])
          @model.get('comments').reset response.content.children, {silent: false}
          @initCommentViews()
          $showComments.removeClass("first-time")
          rebindHideEvents()

  initCommentViews: ->
    @$el.children(".comments").children(".comment").each (index, elem) =>
      model = @model.get('comments').find $(elem).attr("_id")
      if not model.view
        commentView = new CommentView el: elem, model: model

  hideSingleThread: ->
    $threadTitle = @$(".thread-title")
    $hideComments = @$(".discussion-hide-comments")
    $hideComments.removeClass("discussion-hide-comments")
                 .addClass("discussion-show-comments")
    @$el.children(".comments").hide()
    $threadTitle.unbind('click').click @showSingleThread
    $hideComments.unbind('click').click @showSingleThread
    prevHtml = $hideComments.html()
    $hideComments.html prevHtml.replace "Hide", "Show"

  reply: ->
    $replyView = @$(".discussion-reply-new")
    if $replyView.length
      $replyView.show()
    else
      thread_id = if @model.get('type') == "comment" then @model.get('thread_id') else @model.id
      view =
        id: @model.id
        showWatchCheckbox: not DiscussionUtil.isSubscribed(thread_id, "thread")
      @$discussionContent.append Mustache.render DiscussionUtil.replyTemplate, view
      DiscussionUtil.makeWmdEditor @$el, @$local, "reply-body"
      @$(".discussion-submit-post").click @submitReply
      @$(".discussion-cancel-post").click @cancelReply
    @$(".discussion-reply").hide()
    @$(".discussion-edit").hide()

  cancelReply: ->
    $replyView = @$(".discussion-reply-new")
    if $replyView.length
      $replyView.hide()
    @$(".discussion-reply").show()
    @$(".discussion-edit").show()

  unvote: (event) ->
    url = DiscussionUtil.urlFor("undo_vote_for_#{@model.get('type')}", @model.id)
    DiscussionUtil.safeAjax
      $elem: @$(".discussion-vote")
      url: url
      type: "POST"
      dataType: "json"
      success: (response, textStatus) =>
        if textStatus == "success"
          @$(".discussion-vote").removeClass("voted")
          @$(".discussion-votes-point").html response.votes.point

  vote: (event) ->
    $elem = $(event.target)
    if $elem.hasClass("voted")
      @unvote(event)
    else
      value = $elem.attr("value")
      url = Discussion.urlFor("#{value}vote_#{@model.get('type')}", @model.id)
      DiscussionUtil.safeAjax
        $elem: @$(".discussion-vote")
        url: url
        type: "POST"
        dataType: "json"
        success: (response, textStatus) =>
          if textStatus == "success"
            @$(".discussion-vote").removeClass("voted")
            @$(".discussion-vote-#{value}").addClass("voted")
            @$(".discussion-votes-point").html response.votes.point

  endorse: (event) ->
    url = DiscussionUtil.urlFor('endorse_comment', id)
    endorsed = not @model.get('endorsed')
    Discussion.safeAjax
      $elem: $(event.target)
      url: url
      type: "POST"
      dataType: "json"
      data: {endorsed: endorsed}
      success: (response, textStatus) ->
        if textStatus == "success"
          if endorsed
            @$el.addClass("endorsed")
          else
            @$el.removeClass("endorsed")

  close: (event) ->
    url = DiscussionUtil.urlFor('openclose_thread', @model.id)
    closed = undefined
    text = $(event.target).text()
    if text.match(/Close/)
      closed = true
    else if text.match(/[Oo]pen/)
      closed = false
    else
      console.log "Unexpected text " + text + "for open/close thread."
    Discussion.safeAjax
      $elem: $(event.target)
      url: url
      type: "POST"
      dataType: "json"
      data: {closed: closed}
      success: (response, textStatus) =>
        if textStatus == "success"
          if closed
            @$el.addClass("closed")
            $(event.target).text "Re-open Thread"
          else
            @$el.removeClass("closed")
            $(event.target).text "Close Thread"
      error: (response, textStatus, e) ->
        console.log e

  edit: ->
    $local(".discussion-content-wrapper").hide()
    $editView = $local(".discussion-content-edit")
    if $editView.length
      $editView.show()
    else
      view = {
        id: id
        title: $local(".thread-raw-title").html()
        body: $local(".thread-raw-body").html()
        tags: $local(".thread-raw-tags").html()
      }
      $discussionContent.append Mustache.render Discussion.editThreadTemplate, view
      Discussion.makeWmdEditor $content, $local, "thread-body-edit"
      $local(".thread-tags-edit").tagsInput Discussion.tagsInputOptions()
      $local(".discussion-submit-update").unbind("click").click -> handleSubmitEditThread(this)
      $local(".discussion-cancel-update").unbind("click").click -> handleCancelEdit(this)

    handleSubmitEditThread = (elem) ->
      url = Discussion.urlFor('update_thread', id)
      title = $local(".thread-title-edit").val()
      body = Discussion.getWmdContent $content, $local, "thread-body-edit"
      tags = $local(".thread-tags-edit").val()
      Discussion.safeAjax
        $elem: $(elem)
        url: url
        type: "POST"
        dataType: 'json'
        data: {title: title, body: body, tags: tags},
        error: Discussion.formErrorHandler($local(".discussion-update-errors"))
        success: (response, textStatus) ->
          Discussion.clearFormErrors($local(".discussion-update-errors"))
          $discussionContent.replaceWith(response.html)
          Discussion.extendContentInfo response.content['id'], response['annotated_content_info']
          Discussion.initializeContent($content)
          Discussion.bindContentEvents($content)
  delete: ->
    if $content.hasClass("thread")
      url = Discussion.urlFor('delete_thread', id)
      c = confirm "Are you sure to delete thread \"" + $content.find("a.thread-title").text() + "\"?"
    else
      url = Discussion.urlFor('delete_comment', id)
      c = confirm "Are you sure to delete this comment? "
    if c != true
      return
    Discussion.safeAjax
      $elem: $(elem)
      url: url
      type: "POST"
      dataType: "json"
      data: {}
      success: (response, textStatus) =>
        if textStatus == "success"
          $(content).remove()
      error: (response, textStatus, e) ->
        console.log e

  events:
    "click .thread-title": "showSingleThread"
    "click .discussion-show-comments": "showSingleThread"
    "click .discussion-hide-comments": "hideSingleThread"
    "click .discussion-reply-thread": "reply"
    "click .discussion-reply-comment": "reply"
    "click .discussion-cancel-reply": "cancelReply"
    "click .discussion-vote-up": "vote"
    "click .discussion-vote-down": "vote"
    "click .admin-endorse": "endorse"
    "click .admin-openclose": "close"
    "click .admin-edit": "edit"
    "click .admin-delete": "delete"

  initLocal: ->
    @$local = @$el.children(".local")
    @$delegateElement = @$local

  initFollowThread: ->
    $el.children(".discussion-content")
       .find(".follow-wrapper")
       .append(DiscussionUtil.subscriptionLink('thread', id))

  initVote: ->
    if @model.isUpvoted()
      @$(".discussion-vote-up").addClass("voted")
    else if @model.isDownvoted()
      @$(".discussion-vote-down").addClass("voted")

  initBody: ->
    $contentBody = @$(".content-body")
    $contentBody.html DiscussionUtil.postMathJaxProcessor DiscussionUtil.markdownWithHighlight $contentBody.html()
    MathJax.Hub.Queue ["Typeset", MathJax.Hub, $contentBody.attr("id")]

  initActions: ->
    for action, elemSelector of @model.actions
      if not @model.can action
        @$(elemSelector).remove()

  initTimeago: ->
    @$("span.timeago").timeago()

  initialize: ->
    @model.view = @
    @initLocal()
    @initVote()
    @initTimeago()
    @initBody()
    @initActions()
    @initCommentViews()
    
class @Thread extends @Content

class @ThreadView extends @ContentView

class @Comment extends @Content

class @CommentView extends @ContentView

class @Comments extends Backbone.Collection

  model: Comment

  initialize: ->
    
    @bind "add", (item) =>
      item.collection = @

  find: (id) ->
    _.first @where(id: id)
