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

      $(document).keydown $.proxy(@handleKeyDown, @)

      $('div.help-wrapper')
        .focusin($.proxy @helpOnFocus, @)
        .focusout($.proxy @helpOnBlur, @)

  toggle: (event) ->
    event.preventDefault()
    $calc = $('.calc')
    $calcWrapper = $('#calculator_wrapper')
    text = gettext('Open Calculator')
    isExpanded = false

    $('div.calc-main').toggleClass 'open'
    if $calc.hasClass('closed')
      $calcWrapper
        .find('input, a')
        .attr 'tabindex', -1
    else
      text = gettext('Close Calculator')
      isExpanded = true

      $calcWrapper
        .find('input, a,')
        .attr 'tabindex', 0
      # TODO: Investigate why doing this without the timeout causes it to jump
      # down to the bottom of the page. I suspect it's because it's putting the
      # focus on the text field before it transitions onto the page.
      setTimeout (-> $calcWrapper.find('#calculator_input').focus()), 100

    $calc
      .attr
        'title': text
        'aria-expanded': isExpanded
      .text text

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
    $('.help')
      .addClass('shown')
      .attr('aria-hidden', false)

  helpHide: ->
    if not @isFocusedHelp
      $('.help')
        .removeClass('shown')
        .attr('aria-hidden', true)

  handleKeyDown: (e) ->
    ESC = 27
    if e.which is ESC and $('.help').hasClass 'shown'
      @isFocusedHelp = false
      @helpHide()

  calculate: ->
    $.getWithPrefix '/calculate', { equation: $('#calculator_input').val() }, (data) ->
      $('#calculator_output')
        .val(data.result)
        .focus()
