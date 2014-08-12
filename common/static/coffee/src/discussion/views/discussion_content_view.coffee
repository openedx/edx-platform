if Backbone?
  class @DiscussionContentView extends Backbone.View


    events:
      "click .discussion-flag-abuse": "toggleFlagAbuse"
      "keydown .discussion-flag-abuse":
        (event) -> DiscussionUtil.activateOnSpace(event, @toggleFlagAbuse)

    attrRenderer:
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

      can_openclose:
        enable: -> @$(".action-close").closest("li").show()
        disable: -> @$(".action-close").closest("li").hide()

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

  class @DiscussionContentShowView extends DiscussionContentView
    events:
      "click .action-follow": "toggleFollow"
      "click .action-answer": "toggleEndorse"
      "click .action-endorse": "toggleEndorse"
      "click .action-vote": "toggleVote"
      "click .action-more": "showSecondaryActions"
      "click .action-pin": "togglePin"
      "click .action-edit": "edit"
      "click .action-delete": "_delete"
      "click .action-report": "toggleReport"
      "click .action-close": "toggleClose"

    updateButtonState: (selector, checked) =>
      $button = @$(selector)
      $button.toggleClass("is-checked", checked)
      $button.attr("aria-checked", checked)

    attrRenderer: $.extend({}, DiscussionContentView.prototype.attrRenderer, {
      subscribed: (subscribed) ->
        @updateButtonState(".action-follow", subscribed)

      endorsed: (endorsed) ->
        selector = if @model.get("thread").get("thread_type") == "question" then ".action-answer" else ".action-endorse"
        @updateButtonState(selector, endorsed)
        $button = @$(selector)
        $button.toggleClass("is-clickable", @model.canBeEndorsed())
        $button.toggleClass("is-checked", endorsed)
        if endorsed || @model.canBeEndorsed()
          $button.removeAttr("hidden")
        else
          $button.attr("hidden", "hidden")

      votes: (votes) ->
        selector = ".action-vote"
        @updateButtonState(selector, window.user.voted(@model))
        button = @$el.find(selector)
        numVotes = votes.up_count
        button.find(".js-sr-vote-count").html(
          interpolate(gettext("currently %(numVotes)s votes"), {numVotes: numVotes}, true)
        )
        button.find(".js-visual-vote-count").html("" + numVotes)

      pinned: (pinned) ->
        @updateButtonState(".action-pin", pinned)

      abuse_flaggers: (abuse_flaggers) ->
        flagged = (
          window.user.id in abuse_flaggers or
          (DiscussionUtil.isFlagModerator and abuse_flaggers.length > 0)
        )
        @updateButtonState(".action-report", flagged)

      closed: (closed) ->
        @updateButtonState(".action-close", closed)
        @$(".post-status-closed").toggle(closed)
    })

    showSecondaryActions: (event) =>
      event.preventDefault()
      event.stopPropagation()
      @$(".action-more").addClass("is-expanded")
      @$(".post-actions-dropdown, .response-actions-dropdown, .comment-actions-dropdown").addClass("is-expanded")
      $("body").on("click", @hideSecondaryActions)

    hideSecondaryActions: (event) =>
      event.preventDefault()
      event.stopPropagation()
      @$(".action-more").removeClass("is-expanded")
      @$(".post-actions-dropdown, .response-actions-dropdown, .comment-actions-dropdown").removeClass("is-expanded")
      $("body").off("click", @hideSecondaryActions)

    toggleFollow: (event) =>
      event.preventDefault()
      if not @model.get("subscribed")
        @model.follow()
        url = @model.urlFor("follow")
      else
        @model.unfollow()
        url = @model.urlFor("unfollow")
      DiscussionUtil.safeAjax
        url: url
        type: "POST"

    toggleEndorse: (event) =>
      event.preventDefault()
      if not @model.canBeEndorsed()
        return
      url = @model.urlFor('endorse')
      newEndorsed = not @model.get('endorsed')
      endorsement = {
        "username": window.user.get("username"),
        "time": new Date().toISOString()
      }
      @model.set(
        "endorsed": newEndorsed
        "endorsement": if newEndorsed then endorsement else null
      )
      @trigger "comment:endorse", newEndorsed
      DiscussionUtil.safeAjax
        url: url
        data:
          endorsed: newEndorsed
        type: "POST"

    toggleVote: (event) =>
      event.preventDefault()
      if window.user.voted(@model)
        window.user.unvote(@model)
        url = @model.urlFor("unvote")
      else
        window.user.vote(@model)
        url = @model.urlFor("upvote")
      DiscussionUtil.safeAjax
        url: url
        type: "POST"

    togglePin: (event) =>
      event.preventDefault()
      newPinned = not @model.get("pinned")
      if newPinned
        url = @model.urlFor("pinThread")
      else
        url = @model.urlFor("unPinThread")
      @model.set("pinned", newPinned)
      DiscussionUtil.safeAjax
        url: url
        type: "POST"
        error: =>
          if newPinned
            msg = gettext("We had some trouble pinning this thread. Please try again.")
          else
            msg = gettext("We had some trouble unpinning this thread. Please try again.")
          DiscussionUtil.discussionAlert(gettext("Sorry"), msg)
          @model.set("pinned", not newPinned)

    toggleReport: (event) =>
      event.preventDefault()
      newFlaggers = _.clone(@model.get("abuse_flaggers"))
      if window.user.id in @model.get("abuse_flaggers") or (DiscussionUtil.isFlagModerator and @model.get("abuse_flaggers").length > 0)
        url = @model.urlFor("unFlagAbuse")
        newFlaggers.pop(window.user.id)
      else
        url = @model.urlFor("flagAbuse")
        newFlaggers.push(window.user.id)
      @model.set("abuse_flaggers", newFlaggers)
      DiscussionUtil.safeAjax
        url: url
        type: "POST"

    toggleClose: (event) =>
      event.preventDefault()
      url = @model.urlFor("close")
      newClosed = not @model.get("closed")
      @model.set("closed", newClosed)
      DiscussionUtil.safeAjax
        url: url
        data:
          closed: newClosed
        type: "POST"
