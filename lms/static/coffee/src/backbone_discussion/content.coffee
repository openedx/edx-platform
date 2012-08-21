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

class @ContentView extends Backbone.View

  $: (selector) ->
    @$local.find(selector)

  showSingleThread: (event) ->

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

  hideSingleThread: ->

  reply: ->

  cancelReply: ->

  endorse: ->

  close: ->

  edit: ->

  delete: ->

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
    
class @Thread extends @Content

class @ThreadView extends @ContentView

class @Comment extends @Content

class @Comments extends Backbone.Collection
  model: Comment
