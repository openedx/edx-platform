AjaxPrefix.addAjaxPrefix(jQuery, -> $("meta[name='path_prefix']").attr('content'))

$ ->
  $.ajaxSetup
    headers : { 'X-CSRFToken': $.cookie 'csrftoken' }
    dataType: 'json'

  window.onTouchBasedDevice = ->
    navigator.userAgent.match /iPhone|iPod|iPad|Android/i

  $('body').addClass 'touch-based-device' if onTouchBasedDevice()

  # $("a[rel*=leanModal]").leanModal()
  $('#csrfmiddlewaretoken').attr 'value', $.cookie('csrftoken')

  new Calculator
  new FeedbackForm
  if $('body').hasClass('courseware')
    Courseware.start()

  window.postJSON = (url, data, callback) ->
    $.postWithPrefix url, data, callback

  $('#login').click ->
    $('#login_form input[name="email"]').focus()
    false

  $('#signup').click ->
    $('#signup-modal input[name="email"]').focus()
    false

  # fix for ie
  if !Array::indexOf
  	Array::indexOf = (obj, start = 0) ->
  	  for ele, i in this[start..]
        if ele is obj
          return i + start
        return -1
