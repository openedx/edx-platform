class @DiscussionThreadView extends Backbone.View
  events:
    "click .discussion-vote-up": "toggleVote"
    "click .dogear": "toggleFollowing"
  template: _.template($("#thread-template").html())

  initialize: (options) ->
    @model.bind "change", @updateModelDetails
    @$el.html(@template(@model.toJSON()))

  updateModelDetails: =>
    @$(".votes-count-number").html(@model.get("votes")["up_count"])

  render: ->
    if window.user.following(@model)
      @$(".dogear").addClass("is-followed")

    if window.user.voted(@model)
      @$(".vote-btn").addClass("is-cast")
    @$("span.timeago").timeago()
    DiscussionUtil.makeWmdEditor @$el, $.proxy(@$, @), "reply-body"
    @renderResponses()
    @

  renderResponses: ->
    $.ajax @model.id, success: (data, textStatus, xhr) =>
      comments = new Comments(data['content']['children'])
      comments.each @renderResponse

  renderResponse: (response) =>
      view = new ThreadResponseView(model: response)
      view.on "comment:add", @addComment
      view.render()
      @$(".responses").append(view.el)

  addComment: =>
    @model.trigger "comment:add"

  toggleVote: ->
    @$(".vote-btn").toggleClass("is-cast")
    if @$(".vote-btn").hasClass("is-cast")
      @vote()
    else
      @unvote()
    false

  toggleFollowing: (event) ->
    $elem = $(event.target)
    @$(".dogear").toggleClass("is-followed")
    url = null
    if @$(".dogear").hasClass("is-followed")
      @model.follow()
      url = @model.urlFor("follow")
    else
      @model.unfollow()
      url = @model.urlFor("unfollow")
    DiscussionUtil.safeAjax
      $elem: $elem
      url: url
      type: "POST"

  vote: ->
    url = @model.urlFor("upvote")
    @$(".votes-count-number").html(parseInt(@$(".votes-count-number").html()) + 1)
    DiscussionUtil.safeAjax
      $elem: @$(".discussion-vote")
      url: url
      type: "POST"
      success: (response, textStatus) =>
        if textStatus == 'success'
          @model.set(response)

  unvote: ->
    url = @model.urlFor("unvote")
    @$(".votes-count-number").html(parseInt(@$(".votes-count-number").html()) - 1)
    DiscussionUtil.safeAjax
      $elem: @$(".discussion-vote")
      url: url
      type: "POST"
      success: (response, textStatus) =>
        if textStatus == 'success'
          @model.set(response)
