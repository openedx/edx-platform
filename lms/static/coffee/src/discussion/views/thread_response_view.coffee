class @ThreadResponseView extends Backbone.View
  tagName: "li"
  template: _.template($("#thread-response-template").html())
  events:
      "click .vote-btn": "toggleVote"
      "submit form": "submitComment"

  render: ->
    @$el.html(@template(@model.toJSON()))
    if window.user.voted(@model)
      @$(".vote-btn").addClass("is-cast")
    @$(".posted-details").timeago()
    @convertMath()
    @renderComments()
    @

  convertMath: ->
    element = @$(".response-body")
    element.html DiscussionUtil.postMathJaxProcessor DiscussionUtil.markdownWithHighlight element.html()
    MathJax.Hub.Queue ["Typeset", MathJax.Hub, element[0]]

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

  submitComment: (event) ->
    url = @model.urlFor('reply')
    body = @$(".comment-form-input").val()
    if not body.trim().length
      return false
    comment = new Comment(body: body, created_at: (new Date()).toISOString(), username: window.user.get("username"))
    @renderComment(comment)
    @trigger "comment:add"
    @$(".comment-form-input").val("")

    DiscussionUtil.safeAjax
      $elem: $(event.target)
      url: url
      type: "POST"
      dataType: 'json'
      data:
        body: body
       
    false
