jQuery.postWithPrefix = (url, data, callback, type) ->
  $.post("#{Courseware.prefix}#{url}", data, callback, type)

jQuery.getWithPrefix = (url, data, callback, type) ->
  $.get("#{Courseware.prefix}#{url}", data, callback, type)

$ ->
  $.ajaxSetup
    headers : { 'X-CSRFToken': $.cookie 'csrftoken' }
    dataType: 'json'

  window.onTouchBasedDevice = ->
    navigator.userAgent.match /iPhone|iPod|iPad/i

  $('body').addClass 'touch-based-device' if onTouchBasedDevice()

  # $("a[rel*=leanModal]").leanModal()
  $('#csrfmiddlewaretoken').attr 'value', $.cookie('csrftoken')

  new Calculator
  new FeedbackForm
  if $('body').hasClass('courseware')
    Courseware.start()

  # Preserved for backward compatibility
  window.submit_circuit = (circuit_id) ->
    $("input.schematic").each (index, element) ->
      element.schematic.update_value()

    schematic_value $("#schematic_#{circuit_id}").attr("value")
    $.postWithPrefix "/save_circuit/#{circuit_id}", schematic: schematic_value, (data) ->
      alert('Saved') if data.results == 'success'

  window.postJSON = (url, data, callback) ->
    $.postWithPrefix url, data, callback
