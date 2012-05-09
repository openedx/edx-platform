$ ->
  $.ajaxSetup
    headers : { 'X-CSRFToken': $.cookie 'csrftoken' }

  window.onTouchBasedDevice = ->
    navigator.userAgent.match /iPhone|iPod|iPad/i

  $("a[rel*=leanModal]").leanModal()

  if $('body').hasClass('courseware')
    Courseware.start()
