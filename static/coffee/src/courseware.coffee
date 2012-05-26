class window.Courseware
  @bind: ->
    @Navigation.bind()

  class @Navigation
    @bind: ->
      if $('#accordion').length
        navigation = new Navigation
        active = $('#accordion ul:has(li.active)').index('#accordion ul')
        $('#accordion').bind('accordionchange', navigation.log).accordion
          active: if active >= 0 then active else 1
          header: 'h3'
          autoHeight: false
        $('#open_close_accordion a').click navigation.toggle

    log: (event, ui) ->
      log_event 'accordion',
        newheader: ui.newHeader.text()
        oldheader: ui.oldHeader.text()

    toggle: ->
      $('.course-wrapper').toggleClass('closed')
