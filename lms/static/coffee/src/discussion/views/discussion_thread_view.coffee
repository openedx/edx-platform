class @DiscussionThreadView extends DiscussionContentView

  abilityRenderer:
    editable:
      enable: -> @$(".action-edit").closest("li").show()
      disable: -> @$(".action-edit").closest("li").hide()
    can_delete:
      enable: -> @$(".action-delete").closest("li").show()
      disable: -> @$(".action-delete").closest("li").hide()
    can_endorse:
      enable: ->
        @$(".action-endorse").css("cursor", "auto")
      disable: ->
        @$(".action-endorse").css("cursor", "default")

  events:
    "click .discussion-vote": "toggleVote"
    "click .action-follow": "toggleFollowing"
    "click .discussion-submit-post": "submitComment"
    "click .action-edit": "edit"
    "click .action-delete": "delete"

  template: _.template($("#thread-template").html())

  initialize: ->
    @model.on "change", @updateModelDetails

  render: ->
    @$el.html(@template(@model.toJSON()))
    @renderDogear()
    @renderVoted()
    @$("span.timeago").timeago()
    Markdown.makeWmdEditor @$(".reply-body"), "", DiscussionUtil.urlFor("upload"), (text) -> DiscussionUtil.postMathJaxProcessor(text)
    @convertMath()
    @renderResponses()
    @

  renderDogear: ->
    if window.user.following(@model)
      @$(".dogear").addClass("is-followed")

  renderVoted: =>
    if window.user.voted(@model)
      @$("[data-role=discussion-vote]").addClass("is-cast")
    else
      @$("[data-role=discussion-vote]").removeClass("is-cast")

  updateModelDetails: =>
    @renderVoted()
    @$("[data-role=discussion-vote] .votes-count-number").html(@model.get("votes")["up_count"])

  convertMath: ->
    element = @$(".post-body")
    element.html DiscussionUtil.postMathJaxProcessor(element.html())
    MathJax.Hub.Queue ["Typeset", MathJax.Hub, element.attr("id")]

  renderResponses: ->
    DiscussionUtil.safeAjax
      url: "/courses/#{$$course_id}/discussion/forum/#{@model.get('commentable_id')}/threads/#{@model.id}"
      success: (data, textStatus, xhr) =>
        @$(".loading").remove()
        Content.loadContentInfos(data['annotated_content_info'])
        comments = new Comments(data['content']['children'])
        comments.each @renderResponse

  renderResponse: (response) =>
      view = new ThreadResponseView(model: response)
      view.on "comment:add", @addComment
      view.render()
      @$(".responses").append(view.el)

  addComment: =>
    @model.trigger "comment:add"

  toggleVote: (event) ->
    event.preventDefault()
    if window.user.voted(@model)
      @unvote()
    else
      @vote()

  toggleFollowing: (event) ->
    $elem = $(event.target)
    url = null
    if not @model.get('subscribed')
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
    window.user.vote(@model)
    url = @model.urlFor("upvote")
    DiscussionUtil.safeAjax
      $elem: @$(".discussion-vote")
      url: url
      type: "POST"
      success: (response, textStatus) =>
        if textStatus == 'success'
          @model.set(response)

  unvote: ->
    window.user.unvote(@model)
    url = @model.urlFor("unvote")
    DiscussionUtil.safeAjax
      $elem: @$(".discussion-vote")
      url: url
      type: "POST"
      success: (response, textStatus) =>
        if textStatus == 'success'
          @model.set(response)

  submitComment: (event) ->
    event.preventDefault()
    url = @model.urlFor('reply')
    body = @$("#wmd-input").val()
    response = new Comment(body: body, created_at: (new Date()).toISOString(), username: window.user.get("username"), votes: { up_count: 0 }, endorsed: false)
    @renderResponse(response)
    @addComment()

    DiscussionUtil.safeAjax
      $elem: $(event.target)
      url: url
      type: "POST"
      dataType: 'json'
      data:
        body: body

  edit: ->

  delete: ->

  toggleEndorse: ->
    $elem = $(event.target)
    url = @model.urlFor('endorse')
    endorsed = @model.get('endorsed')
    data = { endorsed: not endorsed }
    DiscussionUtil.safeAjax
      $elem: $elem
      url: url
      data: data
      type: "POST"
      success: (response, textStatus) =>
        @model.set('endorsed', not endorsed)
