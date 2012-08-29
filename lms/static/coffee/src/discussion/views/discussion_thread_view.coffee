class @DiscussionThreadView extends Backbone.View
  events:
    "click .discussion-vote-up": "toggleVote"
    "click .dogear": "toggleFollowing"
  initialize: (options) ->
    @user = options['user']
    @model.bind "change", @updateModelDetails

  updateModelDetails: =>
    @$(".votes-count-number").html(@model.get("votes")["up_count"])

  render: ->
    if @user.following(@model)
      @$(".dogear").addClass("is-followed")

    if @user.voted(@model)
      @$(".vote-btn").addClass("is-cast")

    @

  toggleVote: ->
    @$(".vote-btn").toggleClass("is-cast")
    if @$(".vote-btn").hasClass("is-cast")
      @vote()
    else
      @unvote()

  toggleFollowing: (event) ->
    $elem = $(event.target)
    @$(".dogear").toggleClass("is-followed")
    url = null
    if @$(".dogear").hasClass("is-followed")
      url = @model.urlFor("follow")
    else
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
