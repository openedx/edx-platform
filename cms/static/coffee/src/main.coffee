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
    if jqXHR.responseText
        message = _.str.truncate(jqXHR.responseText, 300)
    else
        message = gettext("This may be happening because of an error with our server or your internet connection. Try refreshing the page or making sure you are online.")
    msg = new CMS.Views.Notification.Error(
        "title": gettext("Studio's having trouble saving your work")
        "message": message
    )
    msg.show()

  window.onTouchBasedDevice = ->
    navigator.userAgent.match /iPhone|iPod|iPad/i

  $('body').addClass 'touch-based-device' if onTouchBasedDevice()
