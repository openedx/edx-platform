$ ->
  $.ajaxSetup
    headers : { 'X-CSRFToken': $.cookie 'csrftoken' }

  window.onTouchBasedDevice = ->
    navigator.userAgent.match /iPhone|iPod|iPad/i

  Calculator.bind()
  Courseware.bind()
  FeedbackForm.bind()
  $("a[rel*=leanModal]").leanModal()

