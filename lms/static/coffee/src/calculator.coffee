class @Calculator
  constructor: ->
    $('.calc').click @toggle
    $('form#calculator').submit(@calculate).submit (e) ->
      e.preventDefault()
    $('div.help-wrapper a')
      .focus($.proxy @helpOnFocus, @)
      .blur($.proxy @helpOnBlur, @)
      .hover(
        $.proxy(@helpShow, @),
        $.proxy(@helpHide, @)
      )
      .click (e) ->
        e.preventDefault()

  toggle: (event) ->
    event.preventDefault()
    $calc = $('.calc')
    $calcWrapper = $('#calculator_wrapper')

    $('div.calc-main').toggleClass 'open'
    if $calc.hasClass('closed')
      $calc.attr 'aria-label', 'Open Calculator'
      $calcWrapper
        .find('input, a')
        .attr 'tabindex', -1
    else
      $calc.attr 'aria-label', 'Close Calculator'
      $calcWrapper
        .find('input, a')
        .attr 'tabindex', null
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

  helpHide: ->
    if not @isFocusedHelp
      $('.help').removeClass 'shown'

  calculate: ->
    $.getWithPrefix '/calculate', { equation: $('#calculator_input').val() }, (data) ->
      $('#calculator_output').val(data.result)
