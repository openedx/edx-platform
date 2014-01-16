if Backbone?
  class @DiscussionThreadShowView extends DiscussionContentView

    events:
      "click .vote-btn":
        (event) -> @toggleVote(event)
      "keydown .vote-btn":
        (event) -> DiscussionUtil.activateOnEnter(event, @toggleVote)
      "click .discussion-flag-abuse": "toggleFlagAbuse"
      "keypress .discussion-flag-abuse":
        (event) -> DiscussionUtil.activateOnEnter(event, toggleFlagAbuse)
      "click .admin-pin": "togglePin"
      "click .action-follow": "toggleFollowing"
      "keypress .action-follow":
        (event) -> DiscussionUtil.activateOnEnter(event, toggleFollowing)
      "click .action-edit": "edit"
      "click .action-delete": "_delete"
      "click .action-openclose": "toggleClosed"

    $: (selector) ->
      @$el.find(selector)

    initialize: ->
      super()
      @model.on "change", @updateModelDetails

    renderTemplate: ->
      @template = _.template($("#thread-show-template").html())
      @template(@model.toJSON())

    render: ->
      @$el.html(@renderTemplate())
      @delegateEvents()
      @renderVote()
      @renderFlagged()
      @renderPinned()
      @renderAttrs()
      @$("span.timeago").timeago()
      @convertMath()
      @highlight @$(".post-body")
      @highlight @$("h1,h3")
      @

    renderFlagged: =>
      if window.user.id in @model.get("abuse_flaggers") or (DiscussionUtil.isFlagModerator and @model.get("abuse_flaggers").length > 0)
        @$("[data-role=thread-flag]").addClass("flagged")  
        @$("[data-role=thread-flag]").removeClass("notflagged")
        @$(".discussion-flag-abuse").attr("aria-pressed", "true")
        @$(".discussion-flag-abuse .flag-label").html(gettext("Misuse Reported"))
      else
        @$("[data-role=thread-flag]").removeClass("flagged")  
        @$("[data-role=thread-flag]").addClass("notflagged")      
        @$(".discussion-flag-abuse").attr("aria-pressed", "false")
        @$(".discussion-flag-abuse .flag-label").html(gettext("Report Misuse"))

    renderPinned: =>
      if @model.get("pinned")
        @$("[data-role=thread-pin]").addClass("pinned")  
        @$("[data-role=thread-pin]").removeClass("notpinned")  
        @$(".discussion-pin .pin-label").html(gettext("Pinned"))
      else
        @$("[data-role=thread-pin]").removeClass("pinned")  
        @$("[data-role=thread-pin]").addClass("notpinned")  
        @$(".discussion-pin .pin-label").html(gettext("Pin Thread"))


    updateModelDetails: =>
      @renderVote()
      @renderFlagged()
      @renderPinned()

    convertMath: ->
      element = @$(".post-body")
      element.html DiscussionUtil.postMathJaxProcessor DiscussionUtil.markdownWithHighlight element.text()
      MathJax.Hub.Queue ["Typeset", MathJax.Hub, element[0]]

    edit: (event) ->
      @trigger "thread:edit", event

    _delete: (event) ->
      @trigger "thread:_delete", event

    togglePin: (event) ->
      event.preventDefault()
      if @model.get('pinned')
        @unPin()
      else
        @pin()
      
    pin: ->
      url = @model.urlFor("pinThread")
      DiscussionUtil.safeAjax
        $elem: @$(".discussion-pin")
        url: url
        type: "POST"
        success: (response, textStatus) =>
          if textStatus == 'success'
            @model.set('pinned', true)
        error: =>
          $('.admin-pin').text(gettext("Pinning is not currently available"))
       
    unPin: ->
      url = @model.urlFor("unPinThread")
      DiscussionUtil.safeAjax
        $elem: @$(".discussion-pin")
        url: url
        type: "POST"
        success: (response, textStatus) =>
          if textStatus == 'success'
            @model.set('pinned', false)


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
      if el.html()
        el.html(el.html().replace(/&lt;mark&gt;/g, "<mark>").replace(/&lt;\/mark&gt;/g, "</mark>"))

  class @DiscussionThreadInlineShowView extends DiscussionThreadShowView
    renderTemplate: ->
      @template = DiscussionUtil.getTemplate('_inline_thread_show')
      params = @model.toJSON()
      if @model.get('username')?
        params = $.extend(params, user:{username: @model.username, user_url: @model.user_url})
      Mustache.render(@template, params)

     
