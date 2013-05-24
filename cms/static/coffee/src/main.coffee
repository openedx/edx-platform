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

  $(document).ajaxError (event, jqXHR, ajaxSettings, thrownError) ->
    if ajaxSettings.notifyOnError is false
      return
    msg = new CMS.Models.ErrorMessage(
        "title": gettext("Studio's having trouble saving your work")
        "message": jqXHR.responseText || gettext("This may be happening because of an error with our server or your internet connection. Try refreshing the page or making sure you are online.")
    )
    new CMS.Views.Notification({model: msg})

  window.onTouchBasedDevice = ->
    navigator.userAgent.match /iPhone|iPod|iPad/i

  $('body').addClass 'touch-based-device' if onTouchBasedDevice()
