if Backbone?
  class @ThreadResponseShowView extends DiscussionContentView
    events:
        "click .vote-btn": "toggleVote"
        "click .action-endorse": "toggleEndorse"
        "click .action-delete": "_delete"
        "click .action-edit": "edit"
        "click .discussion-flag-abuse": "toggleFlagAbuse"
        "keypress .discussion-flag-abuse": "toggleFlagAbuseKeypress"

    $: (selector) ->
        @$el.find(selector)

    initialize: ->
        super()
        @model.on "change", @updateModelDetails

    renderTemplate: ->
        @template = _.template($("#thread-response-show-template").html())
        @template(@model.toJSON())

    render: ->
      @$el.html(@renderTemplate())
      @delegateEvents()
      if window.user.voted(@model)
        @$(".vote-btn").addClass("is-cast")
        @$(".vote-btn span.sr").html("votes (click to remove your vote)")
      @renderAttrs()
      @renderFlagged()
      @$el.find(".posted-details").timeago()
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
        @$el.prepend('<div class="staff-banner">staff</div>')
      else if DiscussionUtil.isTA(@model.get("user_id"))
        @$el.addClass("community-ta")
        @$el.prepend('<div class="community-ta-banner">Community TA</div>')

    toggleVote: (event) ->
      event.preventDefault()
      @$(".vote-btn").toggleClass("is-cast")
      if @$(".vote-btn").hasClass("is-cast")
        @vote()
        @$(".vote-btn span.sr").html("votes (click to remove your vote)")
      else
        @unvote()
        @$(".vote-btn span.sr").html("votes (click to vote)")

    vote: ->
      url = @model.urlFor("upvote")
      @$(".votes-count-number").html((parseInt(@$(".votes-count-number").html()) + 1) + '<span class="sr"></span>')
      DiscussionUtil.safeAjax
        $elem: @$(".discussion-vote")
        url: url
        type: "POST"
        success: (response, textStatus) =>
          if textStatus == 'success'
            @model.set(response)

    unvote: ->
      url = @model.urlFor("unvote")
      @$(".votes-count-number").html((parseInt(@$(".votes-count-number").html()) - 1)+'<span class="sr"></span>')
      DiscussionUtil.safeAjax
        $elem: @$(".discussion-vote")
        url: url
        type: "POST"
        success: (response, textStatus) =>
          if textStatus == 'success'
            @model.set(response)
            

    edit: (event) ->
        @trigger "response:edit", event

    _delete: (event) ->
        @trigger "response:_delete", event

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

            
    renderFlagged: =>
      if window.user.id in @model.get("abuse_flaggers") or (DiscussionUtil.isFlagModerator and @model.get("abuse_flaggers").length > 0)
        @$("[data-role=thread-flag]").addClass("flagged")  
        @$("[data-role=thread-flag]").removeClass("notflagged")
        @$(".discussion-flag-abuse").attr("aria-pressed", "true")
        @$(".discussion-flag-abuse .flag-label").html("Misuse Reported")
      else
        @$("[data-role=thread-flag]").removeClass("flagged")  
        @$("[data-role=thread-flag]").addClass("notflagged")      
        @$(".discussion-flag-abuse").attr("aria-pressed", "false")
        @$(".discussion-flag-abuse .flag-label").html("Report Misuse")   
        
    updateModelDetails: =>
      @renderFlagged()
