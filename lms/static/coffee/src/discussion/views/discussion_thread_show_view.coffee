class @DiscussionThreadShowView extends DiscussionContentView

  events:
    "click .discussion-vote": "toggleVote"
    "click .action-follow": "toggleFollowing"
    "click .action-edit": "edit"
    "click .action-delete": "delete"
    "click .action-openclose": "toggleClosed"

  template: _.template($("#thread-show-template").html())

  $: (selector) ->
    @$el.find(selector)

  initialize: ->
    super()
    @model.on "change", @updateModelDetails

  render: ->
    @$el.html(@template(@model.toJSON()))
    @delegateEvents()
    @renderDogear()
    @renderVoted()
    @renderAttrs()
    @$("span.timeago").timeago()
    @convertMath()
    @highlight @$(".post-body")
    @highlight @$("h1")
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
    element.html DiscussionUtil.postMathJaxProcessor DiscussionUtil.markdownWithHighlight element.html()
    MathJax.Hub.Queue ["Typeset", MathJax.Hub, element[0]]

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
          @model.set(response, {silent: true})

  unvote: ->
    window.user.unvote(@model)
    url = @model.urlFor("unvote")
    DiscussionUtil.safeAjax
      $elem: @$(".discussion-vote")
      url: url
      type: "POST"
      success: (response, textStatus) =>
        if textStatus == 'success'
          @model.set(response, {silent: true})

  submitComment: (event) ->
    event.preventDefault()
    url = @model.urlFor('reply')
    body = @getWmdContent("reply-body")
    return if not body.trim().length
    @setWmdContent("reply-body", "")
    comment = new Comment(body: body, created_at: (new Date()).toISOString(), username: window.user.get("username"), votes: { up_count: 0 }, endorsed: false, user_id: window.user.get("id"))
    comment.set('thread', @model.get('thread'))
    @renderResponse(comment)
    @model.addComment()

    DiscussionUtil.safeAjax
      $elem: $(event.target)
      url: url
      type: "POST"
      dataType: 'json'
      data:
        body: body
      success: (data, textStatus) =>
        comment.updateInfo(data.annotated_content_info)
        comment.set(data.content)

  edit: (event) ->
    @trigger "thread:edit", event

  delete: (event) ->
    @trigger "thread:delete", event

  toggleClosed: (event) ->
    $elem = $(event.target)
    url = @model.urlFor('close')
    closed = @model.get('closed')
    data = { closed: not closed }
    DiscussionUtil.safeAjax
      $elem: $elem
      url: url
      data: data
      type: "POST"
      success: (response, textStatus) =>
        @model.set('closed', not closed)
        @model.set('ability', response.ability)

  toggleEndorse: (event) ->
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

  highlight: (el) ->
    el.html(el.html().replace(/&lt;mark&gt;/g, "<mark>").replace(/&lt;\/mark&gt;/g, "</mark>"))
