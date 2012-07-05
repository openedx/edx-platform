@CMS =
  Models: {}
  Views: {}

  viewStack: []

  start: ->
    new CMS.Views.Course(el: $('section.main-container')).render()

  replaceView: (view) ->
    @viewStack = [view]
    CMS.trigger('content.show', view)

  pushView: (view) ->
    @viewStack.push(view)
    CMS.trigger('content.show', view)

  popView: ->
    @viewStack.pop()
    if _.isEmpty(@viewStack)
      CMS.trigger('content.hide')
    else
      view = _.last(@viewStack)
      CMS.trigger('content.show', view)
      view.delegateEvents()

_.extend CMS, Backbone.Events

$ ->
  Backbone.emulateHTTP = true

  $.ajaxSetup
    headers : { 'X-CSRFToken': $.cookie 'csrftoken' }

  CMS.start()
