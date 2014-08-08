if Backbone?
  class @ThreadResponseShowView extends DiscussionContentShowView
    initialize: ->
        super()
        @listenTo(@model, "change", @render)

    renderTemplate: ->
        @template = _.template($("#thread-response-show-template").html())
        @template(@model.toJSON())

    render: ->
      @$el.html(@renderTemplate())
      @delegateEvents()
      @renderAttrs()
      @$el.find(".posted-details .timeago").timeago()
      @convertMath()
      @markAsStaff()
      @

    convertMath: ->
      element = @$(".response-body")
      element.html DiscussionUtil.postMathJaxProcessor DiscussionUtil.markdownWithHighlight element.text()
      MathJax.Hub.Queue ["Typeset", MathJax.Hub, element[0]]

    markAsStaff: ->
      if DiscussionUtil.isStaff(@model.get("user_id"))
        @$el.addClass("staff")
        @$el.prepend('<span class="staff-banner">' + gettext('staff') + '</span>')
      else if DiscussionUtil.isTA(@model.get("user_id"))
        @$el.addClass("community-ta")
        @$el.prepend('<span class="community-ta-banner">' + gettext('Community TA') + '</span>')

    edit: (event) ->
        @trigger "response:edit", event

    _delete: (event) ->
        @trigger "response:_delete", event

    renderFlagged: =>
      if window.user.id in @model.get("abuse_flaggers") or (DiscussionUtil.isFlagModerator and @model.get("abuse_flaggers").length > 0)
        @$("[data-role=thread-flag]").addClass("flagged")
        @$("[data-role=thread-flag]").removeClass("notflagged")
        @$(".discussion-flag-abuse").attr("aria-pressed", "true")
        @$(".discussion-flag-abuse").attr("data-tooltip", gettext("Misuse Reported, click to remove report"))
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
