class @Calculator
  constructor: ->
    $('.calc').click @toggle
    $('form#calculator').submit(@calculate).submit (e) ->
      e.preventDefault()
    $('div.help-wrapper a').hover(@helpToggle).click (e) ->
      e.preventDefault()

  toggle: (event) ->
    event.preventDefault()
    $('div.calc-main').toggleClass 'open'
    if $('.calc.closed').length
      $('.calc').attr 'aria-label', 'Open Calculator'
    else
      $('.calc').attr 'aria-label', 'Close Calculator'
      # TODO: Investigate why doing this without the timeout causes it to jump
      # down to the bottom of the page. I suspect it's because it's putting the
      # focus on the text field before it transitions onto the page.
      setTimeout (-> $('#calculator_wrapper #calculator_input').focus()), 100

    $('.calc').toggleClass 'closed'

  helpToggle: ->
    $('.help').toggleClass 'shown'

  calculate: ->
    $.getWithPrefix '/calculate', { equation: $('#calculator_input').val() }, (data) ->
      $('#calculator_output').val(data.result)
