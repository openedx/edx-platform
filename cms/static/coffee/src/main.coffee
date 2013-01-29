AjaxPrefix.addAjaxPrefix(jQuery, -> CMS.prefix)

@CMS =
  Models: {}
  Views: {}

  prefix: $("meta[name='path_prefix']").attr('content')

_.extend CMS, Backbone.Events

$ ->
  Backbone.emulateHTTP = true

  $.ajaxSetup
    headers : { 'X-CSRFToken': $.cookie 'csrftoken' }
    dataType: 'json'

  window.onTouchBasedDevice = ->
    navigator.userAgent.match /iPhone|iPod|iPad/i

  $('body').addClass 'touch-based-device' if onTouchBasedDevice()
