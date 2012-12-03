if Backbone?
  class @DiscussionThreadShowView extends DiscussionContentView

    events:
      "click .discussion-vote": "toggleVote"
      "click .discussion-flag-abuse": "toggleFlagAbuse"
      "click .action-follow": "toggleFollowing"
      "click .action-edit": "edit"
      "click .action-delete": "delete"
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
      @renderDogear()
      @renderVoted()
      @renderFlagged()
      @renderAttrs()
      @$("span.timeago").timeago()
      @convertMath()
      @highlight @$(".post-body")
      @highlight @$("h1,h3")
      @

    renderDogear: ->
      if window.user.following(@model)
        @$(".dogear").addClass("is-followed")

    renderVoted: =>
      if window.user.voted(@model)
        @$("[data-role=discussion-vote]").addClass("is-cast")
      else
        @$("[data-role=discussion-vote]").removeClass("is-cast")
        
    renderFlagged: =>
      if window.user.id in @model.get("abuse_flaggers")
        @$("[data-role=thread-flag]").addClass("flagged")  
        @$("[data-role=thread-flag]").removeClass("notflagged")
      else
        @$("[data-role=thread-flag]").removeClass("flagged")  
        @$("[data-role=thread-flag]").addClass("notflagged")      

    updateModelDetails: =>
      @renderVoted()
      @renderFlagged()
      @$("[data-role=discussion-vote] .votes-count-number").html(@model.get("votes")["up_count"])

    convertMath: ->
      element = @$(".post-body")
      element.html DiscussionUtil.postMathJaxProcessor DiscussionUtil.markdownWithHighlight element.html()
      MathJax.Hub.Queue ["Typeset", MathJax.Hub, element[0]]

    toggleVote: (event) ->
      event.preventDefault()
      if window.user.voted(@model)
        @unvote()
      else
        @vote()

    toggleFlagAbuse: (event) ->
      event.preventDefault()
      if window.user.id in @model.get("abuse_flaggers")
        @unFlagAbuse()
      else
        @flagAbuse()
      @renderFlagged()


    toggleFollowing: (event) ->
      $elem = $(event.target)
      url = null
      if not @model.get('subscribed')
        @model.follow()
        url = @model.urlFor("follow")
      else
        @model.unfollow()
        url = @model.urlFor("unfollow")
      DiscussionUtil.safeAjax
        $elem: $elem
        url: url
        type: "POST"

    vote: ->
      window.user.vote(@model)
      url = @model.urlFor("upvote")
      DiscussionUtil.safeAjax
        $elem: @$(".discussion-vote")
        url: url
        type: "POST"
        success: (response, textStatus) =>
          if textStatus == 'success'
            @model.set(response, {silent: true})

    flagAbuse: ->
      url = @model.urlFor("flagAbuse")
      DiscussionUtil.safeAjax
        $elem: @$(".discussion-flag-abuse")
        url: url
        type: "POST"
        success: (response, textStatus) =>
          if textStatus == 'success'
            ###
            note, we have to clone the array in order to trigger a change event
            that's 5 hours of my life i'll never get back.
            ###
            temp_array = _.clone(@model.get('abuse_flaggers'));
            temp_array.push(window.user.id)
            @model.set('abuse_flaggers', temp_array)

    unvote: ->
      window.user.unvote(@model)
      url = @model.urlFor("unvote")
      DiscussionUtil.safeAjax
        $elem: @$(".discussion-vote")
        url: url
        type: "POST"
        success: (response, textStatus) =>
          if textStatus == 'success'
            @model.set(response, {silent: true})

    unFlagAbuse: ->
      url = @model.urlFor("unFlagAbuse")
      DiscussionUtil.safeAjax
        $elem: @$(".discussion-flag-abuse")
        url: url
        type: "POST"
        success: (response, textStatus) =>
          if textStatus == 'success'
            temp_array = _.clone(@model.get('abuse_flaggers'));
            temp_array.pop(window.user.id)
            @model.set('abuse_flaggers', temp_array)

    edit: (event) ->
      @trigger "thread:edit", event

    delete: (event) ->
      @trigger "thread:delete", event

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
