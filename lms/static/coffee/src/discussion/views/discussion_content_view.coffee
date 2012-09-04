class @DiscussionContentView extends Backbone.View
  
  attrRenderer:
    endorsed: (endorsed) ->
      if endorsed
        @$(".action-endorse").addClass("is-endorsed")
      else
        @$(".action-endorse").removeClass("is-endorsed")

    closed: (closed) ->

    voted: (voted) ->

    votes_point: (votes_point) ->

    comments_count: (comments_count) ->
      
    subscribed: (subscribed) ->

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

  renderPartialAttrs: ->
    for attr, value of @model.changedAttributes()
      if @attrRenderer[attr]
        @attrRenderer[attr].apply(@, [value])

  renderAttrs: ->
    for attr, value of @model.attributes
      if @attrRenderer[attr]
        @attrRenderer[attr].apply(@, [value])

  initialize: ->
    @model.bind('change', @renderPartialAttrs, @)
