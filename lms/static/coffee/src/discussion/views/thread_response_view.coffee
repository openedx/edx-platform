if Backbone?
  class @ThreadResponseView extends DiscussionContentView
    tagName: "li"
    template: _.template($("#thread-response-template").html())

    events:
        "click .vote-btn": "toggleVote"
        "submit .comment-form": "submitComment"
        "click .action-endorse": "toggleEndorse"
        "click .action-delete": "delete"

    render: ->
      @$el.html(@template(@model.toJSON()))
      @initLocal()
      @delegateEvents()
      if window.user.voted(@model)
        @$(".vote-btn").addClass("is-cast")
      @renderAttrs()
      @$el.find(".posted-details").timeago()
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
      comment.set('thread', @model.get('thread'))
      view = new ResponseCommentView(model: comment)
      view.render()
      @$el.find(".comments li:last").before(view.el)

    toggleVote: (event) ->
      event.preventDefault()
      @$(".vote-btn").toggleClass("is-cast")
      if @$(".vote-btn").hasClass("is-cast")
        @vote()
      else
        @unvote()

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
      event.preventDefault()
      url = @model.urlFor('reply')
      body = @$(".comment-form-input").val()
      if not body.trim().length
        return
      comment = new Comment(body: body, created_at: (new Date()).toISOString(), username: window.user.get("username"), user_id: window.user.get("id"))
      @renderComment(comment)
      @trigger "comment:add", comment
      @$(".comment-form-input").val("")

      DiscussionUtil.safeAjax
        $elem: $(event.target)
        url: url
        type: "POST"
        dataType: 'json'
        data:
          body: body

    delete: (event) ->
      event.preventDefault()
      if not @model.can('can_delete')
        return
      console.log $(event.target)
      url = @model.urlFor('delete')
      if not confirm "Are you sure to delete this response? "
        return
      @model.remove()
      @$el.remove()
      $elem = $(event.target)
      DiscussionUtil.safeAjax
        $elem: $elem
        url: url
        type: "POST"
        success: (response, textStatus) =>

    toggleEndorse: (event) ->
      event.preventDefault()
      if not @model.can('can_endorse')
        return
      $elem = $(event.target)
      url = @model.urlFor('endorse')
      endorsed = @model.get('endorsed')
      data = { endorsed: not endorsed }
      @model.set('endorsed', not endorsed)
      @trigger "comment:endorse", not endorsed
      DiscussionUtil.safeAjax
        $elem: $elem
        url: url
        data: data
        type: "POST"
