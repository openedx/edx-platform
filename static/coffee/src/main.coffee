$ ->
  $.ajaxSetup
    headers : { 'X-CSRFToken': $.cookie 'csrftoken' }
    dataType: 'json'

  window.onTouchBasedDevice = ->
    navigator.userAgent.match /iPhone|iPod|iPad/i

  $("a[rel*=leanModal]").leanModal()
  $('#csrfmiddlewaretoken').attr 'value', $.cookie('csrftoken')

  if $('body').hasClass('courseware')
    Courseware.start()

  # Preserved for backward compatibility
  window.submit_circuit = (circuit_id) ->
    $("input.schematic").each (index, element) ->
      element.schematic.update_value()

    schematic_value $("#schematic_#{circuit_id}").attr("value")
    $.post "/save_circuit/#{circuit_id}", schematic: schematic_value, (data) ->
      alert('Saved') if data.results == 'success'
