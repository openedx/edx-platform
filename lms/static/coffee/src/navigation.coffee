class @Navigation
  constructor: ->
    if $('#accordion').length
      # First look for an active section
      active = $('#accordion ul:has(li.active)').index('#accordion ul')
      # if we didn't find one, look for an active chapter
      if active < 0
        active = $('#accordion h3.active').index('#accordion h3')
      # if that didn't work either, default to 0
      if active < 0
        active = 0
      $('#accordion').bind('accordionchange', @log).accordion
        active: active
        header: 'h3'
        autoHeight: false
        heightStyle: 'content'
      $('#accordion .ui-state-active').closest('.chapter').addClass('is-open')
      $('#open_close_accordion a').click @toggle
      $('#accordion').show()
      $('#accordion a').click @setChapter

  log: (event, ui) ->
    Logger.log 'accordion',
      newheader: ui.newHeader.text()
      oldheader: ui.oldHeader.text()

  toggle: ->
    $('.course-wrapper').toggleClass('closed')

  setChapter: ->
    $('#accordion .is-open').removeClass('is-open')
    $(this).closest('.chapter').addClass('is-open')
    