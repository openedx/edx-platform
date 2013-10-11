class @Calculator
  constructor: ->
    $('.calc').click @toggle
    $('form#calculator').submit(@calculate).submit (e) ->
      e.preventDefault()
    $('div.help-wrapper a')
      .hover(
        $.proxy(@helpShow, @),
        $.proxy(@helpHide, @)
      )
      .click (e) ->
        e.preventDefault()
      $('div.help-wrapper')
        .focusin($.proxy @helpOnFocus, @)
        .focusout($.proxy @helpOnBlur, @)

  toggle: (event) ->
    event.preventDefault()
    $calc = $('.calc')
    $calcWrapper = $('#calculator_wrapper')

    $('div.calc-main').toggleClass 'open'
    if $calc.hasClass('closed')
      $calc.attr
        'aria-label': 'Open Calculator'
        'aria-expanded': false
      $calcWrapper
        .find('input, a, dt, dd')
        .attr 'tabindex', -1
    else
      $calc.attr
        'aria-label': 'Close Calculator'
        'aria-expanded': true
      $calcWrapper
        .find('input, a')
        .attr 'tabindex', 0
      # TODO: Investigate why doing this without the timeout causes it to jump
      # down to the bottom of the page. I suspect it's because it's putting the
      # focus on the text field before it transitions onto the page.
      setTimeout (-> $calcWrapper.find('#calculator_input').focus()), 100

    $calc.toggleClass 'closed'

  helpOnFocus: (e) ->
    e.preventDefault()
    @isFocusedHelp = true
    @helpShow()

  helpOnBlur: (e) ->
    e.preventDefault()
    @isFocusedHelp = false
    @helpHide()

  helpShow: ->
    $('.help').addClass 'shown'
    $('#calculator_hint').attr 'aria-expanded', true

  helpHide: ->
    if not @isFocusedHelp
      $('.help').removeClass 'shown'
      $('#calculator_hint').attr 'aria-expanded', false

  calculate: ->
    $.getWithPrefix '/calculate', { equation: $('#calculator_input').val() }, (data) ->
      $('#calculator_output')
        .val(data.result)
        .focus()
