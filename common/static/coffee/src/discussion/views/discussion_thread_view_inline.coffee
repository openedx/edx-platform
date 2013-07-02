if Backbone?
  class @DiscussionThreadInlineView extends DiscussionThreadView
    expanded = false
    events:
      "click .discussion-submit-post": "submitComment"
      "click .expand-post": "expandPost"
      "click .collapse-post": "collapsePost"

    initialize: ->
      super()

    initLocal: ->
      @$local = @$el.children(".discussion-article").children(".local")
      if not @$local.length
        @$local = @$el
      @$delegateElement = @$local

    render: ->
      if @model.has('group_id')
        @template = DiscussionUtil.getTemplate("_inline_thread_cohorted")
      else
        @template = DiscussionUtil.getTemplate("_inline_thread")

      if not @model.has('abbreviatedBody')
        @abbreviateBody()
      params = @model.toJSON()
      @$el.html(Mustache.render(@template, params))
      #@createShowView()

      @initLocal()
      @delegateEvents()
      @renderShowView()
      @renderAttrs()

      # TODO tags commenting out til we decide what to do with tags
      #@renderTags()

      @$("span.timeago").timeago()
      @$el.find('.post-extended-content').hide()
      if @expanded
        @makeWmdEditor "reply-body"
        @renderResponses()
      @
    createShowView: () ->
      
      if @editView?
        @editView.undelegateEvents()
        @editView.$el.empty()
        @editView = null
      @showView = new DiscussionThreadInlineShowView(model: @model)
      @showView.bind "thread:_delete", @_delete
      @showView.bind "thread:edit", @edit

    renderResponses: ->
      #TODO: threadview
      DiscussionUtil.safeAjax
        url: "/courses/#{$$course_id}/discussion/forum/#{@model.get('commentable_id')}/threads/#{@model.id}"
        $loading: @$el
        success: (data, textStatus, xhr) =>
          #          @$el.find(".loading").remove()
          Content.loadContentInfos(data['annotated_content_info'])
          comments = new Comments(data['content']['children'])
          comments.each @renderResponse
          @trigger "thread:responses:rendered"
          @$('.loading').remove()


    toggleClosed: (event) ->
      #TODO: showview
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
      #TODO: showview
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

    abbreviateBody: ->
      abbreviated = DiscussionUtil.abbreviateString @model.get('body'), 140
      @model.set('abbreviatedBody', abbreviated)

    expandPost: (event) =>
      @expanded = true
      @$el.addClass('expanded')
      @$el.find('.post-body').html(@model.get('body'))
      @showView.convertMath()
      @$el.find('.expand-post').css('display', 'none')
      @$el.find('.collapse-post').css('display', 'block')
      @$el.find('.post-extended-content').show()
      @makeWmdEditor "reply-body"
      @renderAttrs()
      if @$el.find('.loading').length
        @renderResponses()

    collapsePost: (event) ->
      @expanded = false
      @$el.removeClass('expanded')
      @$el.find('.post-body').html(@model.get('abbreviatedBody'))
      @showView.convertMath()
      @$el.find('.collapse-post').css('display', 'none')
      @$el.find('.post-extended-content').hide()
      @$el.find('.expand-post').css('display', 'block')

    createEditView: () ->
      super()
      @editView.bind "thread:update", @expandPost
      @editView.bind "thread:update", @abbreviateBody
      @editView.bind "thread:cancel_edit", @expandPost
