if Backbone?
  class @DiscussionThreadView extends DiscussionContentView

    events:
      "click .discussion-submit-post": "submitComment"

    template: _.template($("#thread-template").html())

    $: (selector) ->
      @$el.find(selector)

    initialize: ->
      super()
      @createShowView()

    render: ->
      @$el.html(@template(@model.toJSON()))
      @delegateEvents()

      @renderShowView()
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

    edit: (event) =>
      @createEditView()
      @renderEditView()

    update: (event) =>

      newTitle = @editView.$(".edit-post-title").val()
      newTags  = @editView.$(".edit-post-tags").val()
      newBody  = @editView.$(".edit-post-body textarea").val()

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
              tags: newTags
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
                tags: newTags

              @createShowView()
              @renderShowView()

    createEditView: () ->

      if @showView?
        @showView.undelegateEvents()
        @showView.$el.empty()
        @showView = null

      @editView = new DiscussionThreadEditView(model: @model)
      @editView.bind "thread:update", @update
      @editView.bind "thread:cancel_edit", @cancelEdit

    renderEditView: () ->
      @editView.setElement(@$('.thread-content-wrapper'))
      @editView.render()
      @editView.delegateEvents()

    createShowView: () ->

      if @editView?
        @editView.undelegateEvents()
        @editView.$el.empty()
        @editView = null

      @showView = new DiscussionThreadShowView(model: @model)
      @showView.bind "thread:delete", @delete
      @showView.bind "thread:edit", @edit

    renderShowView: () ->
      @showView.setElement(@$('.thread-content-wrapper'))
      @showView.render()
      @showView.delegateEvents()

    cancelEdit: (event) =>
      @createShowView()
      @renderShowView()


    delete: (event) =>
      url = @model.urlFor('delete')
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
