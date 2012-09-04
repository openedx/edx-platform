class @DiscussionContentView extends Backbone.View
  
  partialRenderer:
    endorsed: (endorsed) ->

    closed: (closed) -> # we should just re-render the whole thread, or update according to new abilities

    voted: (voted) ->
      if voted
        @$(".discussion-vote").addClass("is-cast")
      else
        @$(".discussion-vote").removeClass("is-cast")

    votes_point: (votes_point) ->
      @$(".discussion-vote .votes-count-number").html(votes_point)

    comments_count: (comments_count) ->
      
    subscribed: (subscribed) ->
      if subscribed
        @$(".dogear").addClass("is-followed")
      else
        @$(".dogear").removeClass("is-followed")

    ability: (ability) ->
      console.log "ability changed"
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

  renderPartial: ->
    console.log "changed"
    for attr, value of @model.changedAttributes()
      if @partialRenderer[attr]
        @partialRenderer[attr].apply(@, [value])

  initialize: ->
    @model.bind('change', @renderPartial, @)
