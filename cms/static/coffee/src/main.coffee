AjaxPrefix.addAjaxPrefix(jQuery, -> CMS.prefix)

@CMS =
  Models: {}
  Views: {}

  prefix: $("meta[name='path_prefix']").attr('content')

  viewStack: []

  start: (el) ->
    new CMS.Views.Course(el: el).render()

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
    dataType: 'json'

  window.onTouchBasedDevice = ->
    navigator.userAgent.match /iPhone|iPod|iPad/i

  $('body').addClass 'touch-based-device' if onTouchBasedDevice()


  CMS.start($('section.main-container'))

