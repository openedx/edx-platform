if Backbone?
  class @DiscussionThreadShowView extends DiscussionContentView

    events:
      "click .vote-btn":
        (event) -> @toggleVote(event)
      "keydown .vote-btn":
        (event) -> DiscussionUtil.activateOnSpace(event, @toggleVote)
      "click .discussion-flag-abuse": "toggleFlagAbuse"
      "keydown .discussion-flag-abuse":
        (event) -> DiscussionUtil.activateOnSpace(event, @toggleFlagAbuse)
      "click .admin-pin":
        (event) -> @togglePin(event)
      "keydown .admin-pin":
        (event) -> DiscussionUtil.activateOnSpace(event, @togglePin)
      "click .action-follow": "toggleFollowing"
      "keydown .action-follow":
        (event) -> DiscussionUtil.activateOnSpace(event, @toggleFollowing)
      "click .action-edit": "edit"
      "click .action-delete": "_delete"
      "click .action-openclose": "toggleClosed"

    $: (selector) ->
      @$el.find(selector)

    initialize: (options) ->
      super()
      @mode = options.mode or "inline"  # allowed values are "tab" or "inline"
      if @mode not in ["tab", "inline"]
        throw new Error("invalid mode: " + @mode)
      @model.on "change", @updateModelDetails

    renderTemplate: ->
      @template = _.template($("#thread-show-template").html())
      context = @model.toJSON()
      context.mode = @mode
      @template(context)

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
        @$(".discussion-flag-abuse").attr("data-tooltip", gettext("Click to remove report"))
        ###
        Translators: The text between start_sr_span and end_span is not shown
        in most browsers but will be read by screen readers.
        ###
        @$(".discussion-flag-abuse .flag-label").html(interpolate(gettext("Misuse Reported%(start_sr_span)s, click to remove report%(end_span)s"), {"start_sr_span": "<span class='sr'>", "end_span": "</span>"}, true))
      else
        @$("[data-role=thread-flag]").removeClass("flagged")  
        @$("[data-role=thread-flag]").addClass("notflagged")      
        @$(".discussion-flag-abuse").attr("aria-pressed", "false")
        @$(".discussion-flag-abuse .flag-label").html(gettext("Report Misuse"))

    renderPinned: =>
      pinElem = @$(".discussion-pin")
      pinLabelElem = pinElem.find(".pin-label")
      if @model.get("pinned")
        pinElem.addClass("pinned")
        pinElem.removeClass("notpinned")
        if @model.can("can_openclose")
          ###
          Translators: The text between start_sr_span and end_span is not shown
          in most browsers but will be read by screen readers.
          ###
          pinLabelElem.html(
              interpolate(
                  gettext("Pinned%(start_sr_span)s, click to unpin%(end_span)s"),
                  {"start_sr_span": "<span class='sr'>", "end_span": "</span>"},
                  true
              )
          )
          pinElem.attr("data-tooltip", gettext("Click to unpin"))
          pinElem.attr("aria-pressed", "true")
        else
          pinLabelElem.html(gettext("Pinned"))
          pinElem.removeAttr("data-tooltip")
          pinElem.removeAttr("aria-pressed")
      else
        # If not pinned and not able to pin, pin is not shown
        pinElem.removeClass("pinned")  
        pinElem.addClass("notpinned")  
        pinLabelElem.html(gettext("Pin Thread"))
        pinElem.removeAttr("data-tooltip")
        pinElem.attr("aria-pressed", "false")

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

    togglePin: (event) =>
      event.preventDefault()
      if @model.get('pinned')
        @unPin()
      else
        @pin()
      
    pin: =>
      url = @model.urlFor("pinThread")
      DiscussionUtil.safeAjax
        $elem: @$(".discussion-pin")
        url: url
        type: "POST"
        success: (response, textStatus) =>
          if textStatus == 'success'
            @model.set('pinned', true)
        error: =>
          DiscussionUtil.discussionAlert("Sorry", "We had some trouble pinning this thread. Please try again.")
       
    unPin: =>
      url = @model.urlFor("unPinThread")
      DiscussionUtil.safeAjax
        $elem: @$(".discussion-pin")
        url: url
        type: "POST"
        success: (response, textStatus) =>
          if textStatus == 'success'
            @model.set('pinned', false)
        error: =>
          DiscussionUtil.discussionAlert("Sorry", "We had some trouble unpinning this thread. Please try again.")

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
