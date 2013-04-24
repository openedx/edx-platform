if Backbone?
  class @DiscussionContentView extends Backbone.View

  
    events:
      "click .discussion-flag-abuse": "toggleFlagAbuse"
  
  
    attrRenderer:
      endorsed: (endorsed) ->
        if endorsed
          @$(".action-endorse").show().addClass("is-endorsed")
        else
          if @model.get('ability')?.can_endorse
            @$(".action-endorse").show()
          else
            @$(".action-endorse").hide()
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
        enable: ->
          @$(".action-endorse").show().css("cursor", "auto")
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
      
     
     
    toggleFlagAbuse: (event) ->
      event.preventDefault()
      if window.user.id in @model.get("abuse_flaggers") or (DiscussionUtil.isFlagModerator and @model.get("abuse_flaggers").length > 0)
        @unFlagAbuse()
      else
        @flagAbuse()
      
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
            ###
            temp_array = _.clone(@model.get('abuse_flaggers'));
            temp_array.push(window.user.id)
            @model.set('abuse_flaggers', temp_array)      
       
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
            # if you're an admin, clear this
            if DiscussionUtil.isFlagModerator
                temp_array = []

            @model.set('abuse_flaggers', temp_array)         
