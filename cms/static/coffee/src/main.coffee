define ["domReady", "jquery", "underscore.string", "backbone", "gettext",
        "js/views/feedback_notification",
        "coffee/src/ajax_prefix", "jquery.cookie"],
(domReady, $, str, Backbone, gettext, NotificationView) ->
  main = ->
    AjaxPrefix.addAjaxPrefix jQuery, ->
      $("meta[name='path_prefix']").attr('content')

    window.CMS = window.CMS or {}
    CMS.URL = CMS.URL or {}
    window.onTouchBasedDevice = ->
      navigator.userAgent.match /iPhone|iPod|iPad|Android/i

    _.extend CMS, Backbone.Events
    Backbone.emulateHTTP = true

    $.ajaxSetup
      headers : { 'X-CSRFToken': $.cookie 'csrftoken' }
      dataType: 'json'

    $(document).ajaxError (event, jqXHR, ajaxSettings, thrownError) ->
      if ajaxSettings.notifyOnError is false
          return
      if jqXHR.responseText
        try
          message = JSON.parse(jqXHR.responseText).error
        catch error
          message = str.truncate(jqXHR.responseText, 300)
      else
        message = gettext("This may be happening because of an error with our server or your internet connection. Try refreshing the page or making sure you are online.")
      msg = new NotificationView.Error(
        "title": gettext("Studio's having trouble saving your work")
        "message": message
      )
      msg.show()

    $.postJSON = (url, data, callback) ->
      # shift arguments if data argument was omitted
      if $.isFunction(data)
        callback = data
        data = `undefined`
      $.ajax
        url: url
        type: "POST"
        contentType: "application/json; charset=utf-8"
        dataType: "json"
        data: JSON.stringify(data)
        success: callback

    domReady ->
      if onTouchBasedDevice()
        $('body').addClass 'touch-based-device'

  main()
  return main
