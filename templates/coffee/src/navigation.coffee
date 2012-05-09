class Courseware::Navigation
  constructor: ->
    if $('#accordion').length
      active = $('#accordion ul:has(li.active)').index('#accordion ul')
      $('#accordion').bind('accordionchange', @log).accordion
        active: if active >= 0 then active else 1
        header: 'h3'
        autoHeight: false
      $('#open_close_accordion a').click @toggle

      $('#accordion').show()

  log: (event, ui) ->
    log_event 'accordion',
      newheader: ui.newHeader.text()
      oldheader: ui.oldHeader.text()

  toggle: ->
    $('.course-wrapper').toggleClass('closed')
