if Backbone?
  class @DiscussionContentView extends Backbone.View


    events:
      "click .discussion-flag-abuse": "toggleFlagAbuse"
      "keydown .discussion-flag-abuse":
        (event) -> DiscussionUtil.activateOnSpace(event, @toggleFlagAbuse)

    attrRenderer:
      closed: (closed) ->
        return if not @$(".action-openclose").length
        return if not @$(".post-status-closed").length
        if closed
          @$(".post-status-closed").show()
          @$(".action-openclose").html(@$(".action-openclose").html().replace(gettext("Close"), gettext("Open")))
          @$(".discussion-reply-new").hide()
        else
          @$(".post-status-closed").hide()
          @$(".action-openclose").html(@$(".action-openclose").html().replace(gettext("Open"), gettext("Close")))
          @$(".discussion-reply-new").show()

      voted: (voted) ->

      votes_point: (votes_point) ->

      comments_count: (comments_count) ->

      subscribed: (subscribed) ->
        if subscribed
          @$(".dogear").addClass("is-followed").attr("aria-checked", "true")
        else
          @$(".dogear").removeClass("is-followed").attr("aria-checked", "false")

      ability: (ability) ->
        for action, selector of @abilityRenderer
          if not ability[action]
            selector.disable.apply(@)
          else
            selector.enable.apply(@)

    abilityRenderer:
      editable:
        enable: -> @$(".action-edit").closest("li").show()
        disable: -> @$(".action-edit").closest("li").hide()
      can_delete:
        enable: -> @$(".action-delete").closest("li").show()
        disable: -> @$(".action-delete").closest("li").hide()

      can_endorse:
        enable: ->
          @$(".action-endorse").show()
        disable: ->
          @$(".action-endorse").css("cursor", "default")
          if not @model.get('endorsed')
            @$(".action-endorse").hide()
          else
            @$(".action-endorse").show()

      can_openclose:
        enable: -> @$(".action-openclose").closest("li").show()
        disable: -> @$(".action-openclose").closest("li").hide()

    renderPartialAttrs: ->
      for attr, value of @model.changedAttributes()
        if @attrRenderer[attr]
          @attrRenderer[attr].apply(@, [value])

    renderAttrs: ->
      for attr, value of @model.attributes
        if @attrRenderer[attr]
          @attrRenderer[attr].apply(@, [value])

    makeWmdEditor: (cls_identifier) =>
      if not @$el.find(".wmd-panel").length
        DiscussionUtil.makeWmdEditor @$el, $.proxy(@$, @), cls_identifier

    getWmdEditor: (cls_identifier) =>
      DiscussionUtil.getWmdEditor @$el, $.proxy(@$, @), cls_identifier

    getWmdContent: (cls_identifier) =>
      DiscussionUtil.getWmdContent @$el, $.proxy(@$, @), cls_identifier

    setWmdContent: (cls_identifier, text) =>
      DiscussionUtil.setWmdContent @$el, $.proxy(@$, @), cls_identifier, text


    initialize: ->
      @model.bind('change', @renderPartialAttrs, @)


    toggleFollowing: (event) =>
      event.preventDefault()
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

    toggleFlagAbuse: (event) =>
      event.preventDefault()
      if window.user.id in @model.get("abuse_flaggers") or (DiscussionUtil.isFlagModerator and @model.get("abuse_flaggers").length > 0)
        @unFlagAbuse()
      else
        @flagAbuse()

    flagAbuse: =>
      url = @model.urlFor("flagAbuse")
      DiscussionUtil.safeAjax
        $elem: @$(".discussion-flag-abuse")
        url: url
        type: "POST"
        success: (response, textStatus) =>
          if textStatus == 'success'
            ###
            note, we have to clone the array in order to trigger a change event
            ###
            temp_array = _.clone(@model.get('abuse_flaggers'));
            temp_array.push(window.user.id)
            @model.set('abuse_flaggers', temp_array)

    unFlagAbuse: =>
      url = @model.urlFor("unFlagAbuse")
      DiscussionUtil.safeAjax
        $elem: @$(".discussion-flag-abuse")
        url: url
        type: "POST"
        success: (response, textStatus) =>
          if textStatus == 'success'
            temp_array = _.clone(@model.get('abuse_flaggers'));
            temp_array.pop(window.user.id)
            # if you're an admin, clear this
            if DiscussionUtil.isFlagModerator
                temp_array = []

            @model.set('abuse_flaggers', temp_array)

    renderVote: =>
      button = @$el.find(".vote-btn")
      voted = window.user.voted(@model)
      voteNum = @model.get("votes")["up_count"]
      button.toggleClass("is-cast", voted)
      button.attr("aria-pressed", voted)
      button.attr("data-tooltip", if voted then gettext("remove vote") else gettext("vote"))
      buttonTextFmt =
        if voted
          ngettext(
            "vote (click to remove your vote)",
            "votes (click to remove your vote)",
            voteNum
          )
        else
          ngettext(
            "vote (click to vote)",
            "votes (click to vote)",
            voteNum
          )
      buttonTextFmt = "%(voteNum)s%(startSrSpan)s " + buttonTextFmt + "%(endSrSpan)s"
      buttonText = interpolate(
        buttonTextFmt,
        {voteNum: voteNum, startSrSpan: "<span class='sr'>", endSrSpan: "</span>"},
        true
      )
      button.html("<span class='plus-icon'/>" + buttonText)

    toggleVote: (event) =>
      event.preventDefault()
      if window.user.voted(@model)
        @unvote()
      else
        @vote()

    vote: =>
      window.user.vote(@model)
      url = @model.urlFor("upvote")
      DiscussionUtil.safeAjax
        $elem: @$el.find(".vote-btn")
        url: url
        type: "POST"
        success: (response, textStatus) =>
          if textStatus == 'success'
            @model.set(response)

    unvote: =>
      window.user.unvote(@model)
      url = @model.urlFor("unvote")
      DiscussionUtil.safeAjax
        $elem: @$el.find(".vote-btn")
        url: url
        type: "POST"
        success: (response, textStatus) =>
          if textStatus == 'success'
            @model.set(response)
