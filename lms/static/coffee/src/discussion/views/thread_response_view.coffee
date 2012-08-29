class @ThreadResponseView extends Backbone.View
  tagName: "li"
  template: _.template($("#thread-response-template").html())
  events:
      "click .vote-btn": "toggleVote"
  render: ->
    @$el.html(@template(@model.toJSON()))
    if window.user.voted(@model)
      @$(".vote-btn").addClass("is-cast")
    @$(".posted-details").timeago()
    @renderComments()
    @

  renderComments: ->
      @model.get("comments").each @renderComment

  renderComment: (comment) =>
    view = new ResponseCommentView(model: comment)
    view.render()
    @$(".comments li:last").before(view.el)

  toggleVote: ->
    @$(".vote-btn").toggleClass("is-cast")
    if @$(".vote-btn").hasClass("is-cast")
      @vote()
    else
      @unvote()
    false

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
