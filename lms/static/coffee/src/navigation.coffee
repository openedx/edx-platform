class @Navigation
  constructor: ->
    if $('#accordion').length
      # First look for an active section
      active = $('#accordion div div:has(a.active)').index('#accordion div div')
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
      $('#accordion .ui-state-active').parent().next('div').children('div').addClass('ui-accordion-content-active')
      $('#accordion .ui-state-active').parent().next('div').show()
      $('#accordion .ui-state-active').parent().attr('aria-expanded' , 'true').attr('aria-pressed' , 'true')
      $('#accordion div').filter(':not(.chapter-content-container)').addClass("ui-accordion-content ui-helper-reset ui-widget-content ui-corner-bottom").filter(":not(.ui-accordion-content-active)").hide()
      $('.ui-accordion-content div').attr('aria-hidden', 'false')
      $('.ui-accordion-content-active div').attr('aria-hidden', 'true')
      $('#open_close_accordion a').click @toggle
      $('#accordion').show()
      $('#accordion .chapter').click @setChapter

  log: (event, ui) ->
    Logger.log 'accordion',
      newheader: ui.newHeader.text()
      oldheader: ui.oldHeader.text()

  toggle: ->
    $('.course-wrapper').toggleClass('closed')

  setChapter: ->
    $('#accordion .is-open').removeClass('is-open').attr('aria-expanded' , 'false').attr('aria-pressed' , 'false').find('h3 span').removeClass('ui-icon-triangle-1-s').addClass('ui-icon-triangle-1-e')
    $(this).closest('.chapter').addClass('is-open').attr('aria-expanded' , 'true').attr('aria-pressed' , 'true').find('h3 span').removeClass('ui-icon-triangle-1-e').addClass('ui-icon-triangle-1-s')
    $('.ui-accordion-content-active').attr('aria-hidden', 'true')
    $('.ui-accordion-content-active').parent().hide()
    $('#accordion .ui-accordion-content-active').removeClass('ui-accordion-content-active')
    $(this).closest('.chapter').next('div').children('div').addClass('ui-accordion-content-active')
    $('.ui-accordion-content-active').parent().show().focus()
    $('.ui-accordion-content-active').show()
    $('.ui-accordion-content-active').attr('aria-hidden', 'false')

