if Backbone?
  class @DiscussionThreadView extends DiscussionContentView

    INITIAL_RESPONSE_PAGE_SIZE = 25
    SUBSEQUENT_RESPONSE_PAGE_SIZE = 100

    events:
      "click .discussion-submit-post": "submitComment"
      "click .add-response-btn": "scrollToAddResponse"

    $: (selector) ->
      @$el.find(selector)

    initialize: ->
      super()
      @createShowView()
      @responses = new Comments()

    renderTemplate: ->
      @template = _.template($("#thread-template").html())
      @template(@model.toJSON())

    render: ->
      @$el.html(@renderTemplate())
      @delegateEvents()

      @renderShowView()
      @renderAttrs()

      @$("span.timeago").timeago()
      @makeWmdEditor "reply-body"
      @renderAddResponseButton()
      @responses.on("add", @renderResponse)
      # Without a delay, jQuery doesn't add the loading extension defined in
      # utils.coffee before safeAjax is invoked, which results in an error
      setTimeout((=> @loadInitialResponses()), 100)
      @

    cleanup: ->
      if @responsesRequest?
        @responsesRequest.abort()

    loadResponses: (responseLimit, elem, firstLoad) ->
      @responsesRequest = DiscussionUtil.safeAjax
        url: DiscussionUtil.urlFor('retrieve_single_thread', @model.get('commentable_id'), @model.id)
        data:
          resp_skip: @responses.size()
          resp_limit: responseLimit if responseLimit
        $elem: elem
        $loading: elem
        takeFocus: true
        complete: =>
          @responseRequest = null
        success: (data, textStatus, xhr) =>
          Content.loadContentInfos(data['annotated_content_info'])
          @responses.add(data['content']['children'])
          @renderResponseCountAndPagination(data['content']['resp_total'])
          @trigger "thread:responses:rendered"
        error: (xhr) =>
          if xhr.status == 404
            DiscussionUtil.discussionAlert(
              gettext("Sorry"),
              gettext("The thread you selected has been deleted. Please select another thread.")
            )
          else if firstLoad
            DiscussionUtil.discussionAlert(
              gettext("Sorry"),
              gettext("We had some trouble loading responses. Please reload the page.")
            )
          else
            DiscussionUtil.discussionAlert(
              gettext("Sorry"),
              gettext("We had some trouble loading more responses. Please try again.")
            )

    loadInitialResponses: () ->
      @loadResponses(INITIAL_RESPONSE_PAGE_SIZE, @$el.find(".responses"), true)

    renderResponseCountAndPagination: (responseTotal) =>
      @$el.find(".response-count").html(
        interpolate(
          ngettext(
            "%(numResponses)s response",
            "%(numResponses)s responses",
            responseTotal
          ),
          {numResponses: responseTotal},
          true
        )
      )
      responsePagination = @$el.find(".response-pagination")
      responsePagination.empty()
      if responseTotal > 0
        responsesRemaining = responseTotal - @responses.size()
        showingResponsesText =
          if responsesRemaining == 0
            gettext("Showing all responses")
          else
            interpolate(
              ngettext(
                "Showing first response",
                "Showing first %(numResponses)s responses",
                @responses.size()
              ),
              {numResponses: @responses.size()},
              true
            )
        responsePagination.append($("<span>").addClass("response-display-count").html(
          _.escape(showingResponsesText)
        ))
        if responsesRemaining > 0
          if responsesRemaining < SUBSEQUENT_RESPONSE_PAGE_SIZE
            responseLimit = null
            buttonText = gettext("Load all responses")
          else
            responseLimit = SUBSEQUENT_RESPONSE_PAGE_SIZE
            buttonText = interpolate(
              gettext("Load next %(numResponses)s responses"),
              {numResponses: responseLimit},
              true
            )
          loadMoreButton = $("<button>").addClass("load-response-button").html(
            _.escape(buttonText)
          )
          loadMoreButton.click((event) => @loadResponses(responseLimit, loadMoreButton))
          responsePagination.append(loadMoreButton)

    renderResponse: (response) =>
        response.set('thread', @model)
        view = new ThreadResponseView(model: response)
        view.on "comment:add", @addComment
        view.on "comment:endorse", @endorseThread
        view.render()
        @$el.find(".responses").append(view.el)
        view.afterInsert()

    renderAddResponseButton: ->
      if @model.hasResponses() and @model.can('can_reply')
        @$el.find('div.add-response').show()
      else
        @$el.find('div.add-response').hide()

    scrollToAddResponse: (event) ->
      event.preventDefault()
      form = $(event.target).parents('article.discussion-article').find('form.discussion-reply-new')
      $('html, body').scrollTop(form.offset().top)
      form.find('.wmd-panel textarea').focus()

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
      @renderAddResponseButton()

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

          error: DiscussionUtil.formErrorHandler(@$(".edit-post-form-errors"))
          success: (response, textStatus) =>
              # TODO: Move this out of the callback, this makes it feel sluggish
              @editView.$(".edit-post-title").val("").attr("prev-text", "")
              @editView.$(".edit-post-body textarea").val("").attr("prev-text", "")
              @editView.$(".wmd-preview p").html("")

              @model.set
                title: newTitle
                body: newBody

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

    renderSubView: (view) ->
      view.setElement(@$('.thread-content-wrapper'))
      view.render()
      view.delegateEvents()

    renderEditView: () ->
      @renderSubView(@editView)

    getShowViewClass: () ->
      return DiscussionThreadShowView

    createShowView: () ->

      if @editView?
        @editView.undelegateEvents()
        @editView.$el.empty()
        @editView = null

      showViewClass = @getShowViewClass()
      @showView = new showViewClass(model: @model)
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
      if not confirm gettext("Are you sure you want to delete this post?")
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
