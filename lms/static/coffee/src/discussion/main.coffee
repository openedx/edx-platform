class @DiscussionUser
    constructor: (content_info) ->
        @content_info = content_info

    following: (thread) ->
        @content_info[thread.id]['subscribed'] == true

    voted: (thread) ->
        @content_info[thread.id]['voted'] == 'up'

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

  toggleVote: ->
    @$(".vote-btn").toggleClass("is-cast")
    if @$(".vote-btn").hasClass("is-cast")
      @vote()
    else
      @unvote()

  toggleFollowing: ->
    @$(".dogear").toggleClass("is-followed")

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

$ ->
  window.$$contents = {}
  window.$$discussions = {}
