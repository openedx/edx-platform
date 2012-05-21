class window.Calculator
  @bind: ->
    calculator = new Calculator
    $('.calc').click calculator.toggle
    $('form#calculator').submit(calculator.calculate).submit (e) ->
      e.preventDefault()
    $('div.help-wrapper a').hover(calculator.helpToggle).click (e) ->
      e.preventDefault()

  toggle: ->
    $('li.calc-main').toggleClass 'open'
    $('#calculator_wrapper #calculator_input').focus()
    if $('.calc.closed').length
      $('.calc').attr 'aria-label', 'Open Calculator'
    else
      $('.calc').attr 'aria-label', 'Close Calculator'

    $('.calc').toggleClass 'closed'

  helpToggle: ->
    $('.help').toggleClass 'shown'

  calculate: ->
    $.getJSON '/calculate', { equation: $('#calculator_input').val() }, (data) ->
      $('#calculator_output').val(data.result)
