if Backbone?
  class @DiscussionThreadView extends DiscussionContentView

    events:
      "click .discussion-submit-post": "submitComment"

      # TODO tags
      # Until we decide what to do w/ tags, removing them.
      #"click .thread-tag": "tagSelected"

    $: (selector) ->
      @$el.find(selector)

    initialize: ->
      super()
      @createShowView()

    renderTemplate: ->
      @template = _.template($("#thread-template").html())
      @template(@model.toJSON())

    render: ->
      @$el.html(@renderTemplate())
      @$el.find(".loading").hide()
      @delegateEvents()

      @renderShowView()
      @renderAttrs()

      # TODO tags
      # Until we decide what to do w/ tags, removing them.
      #@renderTags()

      @$("span.timeago").timeago()
      @makeWmdEditor "reply-body"
      @renderResponses()
      @

    cleanup: ->
      if @responsesRequest?
        @responsesRequest.abort()

    # TODO tags
    # Until we decide what to do w/ tags, removing them.
    #renderTags: ->
    #  # tags
    #  for tag in @model.get("tags")
    #    if !tags
    #      tags = $('<div class="thread-tags">')
    #    tags.append("<a href='#' class='thread-tag'>#{tag}</a>")
    #  @$(".post-body").after(tags)

    # TODO tags
    # Until we decide what to do w tags, removing them.
    #tagSelected: (e) ->
    #  @trigger "tag:selected", $(e.target).html()

    renderResponses: ->
      setTimeout(=>
        @$el.find(".loading").show()
      , 200)
      @responsesRequest = DiscussionUtil.safeAjax
        url: DiscussionUtil.urlFor('retrieve_single_thread', @model.get('commentable_id'), @model.id)
        success: (data, textStatus, xhr) =>
          @responsesRequest = null
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
        view.afterInsert()

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
      comment = new Comment(body: body, created_at: (new Date()).toISOString(), username: window.user.get("username"), votes: { up_count: 0 }, abuse_flaggers:[], endorsed: false, user_id: window.user.get("id"))
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

    edit: (event) =>
      @createEditView()
      @renderEditView()

    update: (event) =>

      newTitle = @editView.$(".edit-post-title").val()
      newBody  = @editView.$(".edit-post-body textarea").val()

      # TODO tags
      # Until we decide what to do w/ tags, removing them.
      #newTags  = @editView.$(".edit-post-tags").val()

      url = DiscussionUtil.urlFor('update_thread', @model.id)

      DiscussionUtil.safeAjax
          $elem: $(event.target)
          $loading: $(event.target) if event
          url: url
          type: "POST"
          dataType: 'json'
          async: false # TODO when the rest of the stuff below is made to work properly..
          data:
              title: newTitle
              body: newBody

              # TODO tags
              # Until we decide what to do w/ tags, removing them.
              #tags: newTags

          error: DiscussionUtil.formErrorHandler(@$(".edit-post-form-errors"))
          success: (response, textStatus) =>
              # TODO: Move this out of the callback, this makes it feel sluggish
              @editView.$(".edit-post-title").val("").attr("prev-text", "")
              @editView.$(".edit-post-body textarea").val("").attr("prev-text", "")
              @editView.$(".edit-post-tags").val("")
              @editView.$(".edit-post-tags").importTags("")
              @editView.$(".wmd-preview p").html("")

              @model.set
                title: newTitle
                body: newBody
                tags: response.content.tags

              @createShowView()
              @renderShowView()

              # TODO tags
              # Until we decide what to do w/ tags, removing them.
              #@renderTags()

    createEditView: () ->

      if @showView?
        @showView.undelegateEvents()
        @showView.$el.empty()
        @showView = null

      @editView = new DiscussionThreadEditView(model: @model)
      @editView.bind "thread:update", @update
      @editView.bind "thread:cancel_edit", @cancelEdit

    renderSubView: (view) ->
      view.setElement(@$('.thread-content-wrapper'))
      view.render()
      view.delegateEvents()

    renderEditView: () ->
      @renderSubView(@editView)

    createShowView: () ->

      if @editView?
        @editView.undelegateEvents()
        @editView.$el.empty()
        @editView = null

      @showView = new DiscussionThreadShowView(model: @model)
      @showView.bind "thread:_delete", @_delete
      @showView.bind "thread:edit", @edit

    renderShowView: () ->
      @renderSubView(@showView)

    cancelEdit: (event) =>
      event.preventDefault()
      @createShowView()
      @renderShowView()

    # If you use "delete" here, it will compile down into JS that includes the
    # use of DiscussionThreadView.prototype.delete, and that will break IE8
    # because "delete" is a keyword. So, using an underscore to prevent that.
    _delete: (event) =>
      url = @model.urlFor('_delete')
      if not @model.can('can_delete')
        return
      if not confirm "Are you sure to delete thread \"#{@model.get('title')}\"?"
        return
      @model.remove()
      @showView.undelegateEvents()
      @undelegateEvents()
      @$el.empty()
      $elem = $(event.target)
      DiscussionUtil.safeAjax
        $elem: $elem
        url: url
        type: "POST"
        success: (response, textStatus) =>
