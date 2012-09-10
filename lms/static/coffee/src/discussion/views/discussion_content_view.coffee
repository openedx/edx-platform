if Backbone?
  class @DiscussionContentView extends Backbone.View

    attrRenderer:
      endorsed: (endorsed) ->
        if endorsed
          @$(".action-endorse").addClass("is-endorsed")
        else
          @$(".action-endorse").removeClass("is-endorsed")

      closed: (closed) ->
        return if not @$(".action-openclose").length
        return if not @$(".post-status-closed").length
        if closed
          @$(".post-status-closed").show()
          @$(".action-openclose").html(@$(".action-openclose").html().replace("Close", "Open"))
          @$(".discussion-reply-new").hide()
        else
          @$(".post-status-closed").hide()
          @$(".action-openclose").html(@$(".action-openclose").html().replace("Open", "Close"))
          @$(".discussion-reply-new").show()

      voted: (voted) ->

      votes_point: (votes_point) ->

      comments_count: (comments_count) ->

      subscribed: (subscribed) ->
        if subscribed
          @$(".dogear").addClass("is-followed")
        else
          @$(".dogear").removeClass("is-followed")

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
        enable: -> @$(".action-endorse").css("cursor", "auto")
        disable: -> @$(".action-endorse").css("cursor", "default")
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

    $: (selector) ->
      @$local.find(selector)

    initLocal: ->
      @$local = @$el.children(".local")
      if not @$local.length
        @$local = @$el
      @$delegateElement = @$local

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
      @initLocal()
      @model.bind('change', @renderPartialAttrs, @)
