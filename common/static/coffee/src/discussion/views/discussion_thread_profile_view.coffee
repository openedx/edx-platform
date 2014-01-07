if Backbone?
  class @DiscussionThreadProfileView extends DiscussionContentView
    expanded = false
    events:
      "click .vote-btn":
        (event) -> @toggleVote(event)
      "keydown .vote-btn":
        (event) -> DiscussionUtil.activateOnEnter(event, @toggleVote)
      "click .action-follow": "toggleFollowing"
      "keypress .action-follow":
        (event) -> DiscussionUtil.activateOnEnter(event, toggleFollowing)
      "click .expand-post": "expandPost"
      "click .collapse-post": "collapsePost"

    initLocal: ->
      @$local = @$el.children(".discussion-article").children(".local")
      @$delegateElement = @$local

    initialize: ->
      super()
      @model.on "change", @updateModelDetails

    render: ->
      @template = DiscussionUtil.getTemplate("_profile_thread")
      if not @model.has('abbreviatedBody')
        @abbreviateBody()
      params = $.extend(@model.toJSON(),{expanded: @expanded, permalink: @model.urlFor('retrieve')})
      if not @model.get('anonymous')
        params = $.extend(params, user:{username: @model.username, user_url: @model.user_url})
      @$el.html(Mustache.render(@template, params))
      @initLocal()
      @delegateEvents()
      @renderVote()
      @renderAttrs()
      @$("span.timeago").timeago()
      @convertMath()
      if @expanded
        @renderResponses()
      @

    updateModelDetails: =>
      @renderVote()

    convertMath: ->
      element = @$(".post-body")
      element.html DiscussionUtil.postMathJaxProcessor DiscussionUtil.markdownWithHighlight element.text()
      MathJax.Hub.Queue ["Typeset", MathJax.Hub, element[0]]

    renderResponses: ->
      DiscussionUtil.safeAjax
        url: "/courses/#{$$course_id}/discussion/forum/#{@model.get('commentable_id')}/threads/#{@model.id}"
        $loading: @$el
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
      view.render()
      @$el.find(".responses").append(view.el)

    addComment: =>
      @model.comment()

    edit: ->

    abbreviateBody: ->
      abbreviated = DiscussionUtil.abbreviateString @model.get('body'), 140
      @model.set('abbreviatedBody', abbreviated)

    expandPost: (event) ->
      @expanded = true
      @$el.addClass('expanded')
      @$el.find('.post-body').html(@model.get('body'))
      @convertMath()
      @$el.find('.expand-post').css('display', 'none')
      @$el.find('.collapse-post').css('display', 'block')
      @$el.find('.post-extended-content').show()
      if @$el.find('.loading').length
        @renderResponses()

    collapsePost: (event) ->
      @expanded = false
      @$el.removeClass('expanded')
      @$el.find('.post-body').html(@model.get('abbreviatedBody'))
      @convertMath()
      @$el.find('.collapse-post').css('display', 'none')
      @$el.find('.post-extended-content').hide()
      @$el.find('.expand-post').css('display', 'block')
