class @DiscussionThreadView extends DiscussionContentView

  events:
    "click .discussion-submit-post": "submitComment"

  template: _.template($("#thread-template").html())

  $: (selector) ->
    @$el.find(selector)

  initialize: ->
    super()
    @showView = new DiscussionThreadShowView(model: @model)
    @showView.bind "thread:delete", @delete
    @showView.bind "thread:edit", @edit

  render: ->
    @$el.html(@template(@model.toJSON()))
    @delegateEvents()

    @showView.setElement(@$('.thread-content-wrapper'))
    @showView.render()
    @showView.delegateEvents()

    @renderAttrs()
    @$("span.timeago").timeago()
    @makeWmdEditor "reply-body"
    @renderResponses()
    @

  renderResponses: ->
    DiscussionUtil.safeAjax
      url: "/courses/#{$$course_id}/discussion/forum/#{@model.get('commentable_id')}/threads/#{@model.id}"
      success: (data, textStatus, xhr) =>
        @$el.find(".loading").remove()
        Content.loadContentInfos(data['annotated_content_info'])
        comments = new Comments(data['content']['children'])
        comments.each @renderResponse
        @trigger "thread:responses:rendered"

  renderResponse: (response) =>
      response.set('thread', @model)
      view = new ThreadResponseView(model: response)
      view.on "comment:add", @addComment
      view.on "comment:endorse", @endorseThread
      view.render()
      @$el.find(".responses").append(view.el)

  addComment: =>
    @model.comment()

  endorseThread: (endorsed) =>
    is_endorsed = @$el.find(".is-endorsed").length
    @model.set 'endorsed', is_endorsed

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

  edit: ->

  delete: (event) ->
    url = @model.urlFor('delete')
    if not @model.can('can_delete')
      return
    if not confirm "Are you sure to delete thread \"#{@model.get('title')}\"?"
      return
    @model.remove()
    @$el.empty()
    $elem = $(event.target)
    DiscussionUtil.safeAjax
      $elem: $elem
      url: url
      type: "POST"
      success: (response, textStatus) =>
