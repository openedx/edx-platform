# Keyboard Support

# If focus is on the hint button:
#   * Enter: Open or close hint popup. Select last focused hint item if opening
#   * Space: Open or close hint popup. Select last focused hint item if opening

# If focus is on a hint item:
#   * Left arrow: Select previous hint item
#   * Up arrow: Select previous hint item
#   * Right arrow: Select next hint item
#   * Down arrow: Select next hint item


class @Calculator
  constructor: ->
    @hintButton = $('#calculator_hint')
    @calcInput = $('#calculator_input')
    @hintPopup = $('.help')
    @hintsList = @hintPopup.find('.hint-item')
    @selectHint($('#' + @hintPopup.attr('data-calculator-hint')));

    $('.calc').click @toggle
    $('form#calculator').submit(@calculate).submit (e) ->
      e.preventDefault()

    @hintButton
      .click(($.proxy(@handleClickOnHintButton, @)))

    @hintPopup
      .click(($.proxy(@handleClickOnHintPopup, @)))

    @hintPopup
      .keydown($.proxy(@handleKeyDownOnHint, @))

    $('#calculator_wrapper')
      .keyup($.proxy(@handleKeyUpOnHint, @))

    @handleClickOnDocument = $.proxy(@handleClickOnDocument, @)
    
    @calcInput
      .focus(($.proxy(@inputClickHandler, @)))

  KEY:
    TAB   : 9
    ENTER : 13
    ESC   : 27
    SPACE : 32
    LEFT  : 37
    UP    : 38
    RIGHT : 39
    DOWN  : 40

  toggle: (event) ->
    event.preventDefault()
    $calc = $('.calc')
    $calcWrapper = $('#calculator_wrapper')
    text = gettext('Open Calculator')
    isExpanded = false
    icon = 'fa-calculator'    

    $('.calc-main').toggleClass 'open'
    if $calc.hasClass('closed')
      $calcWrapper
        .attr('aria-hidden', 'true')
    else
      text = gettext('Close Calculator')
      icon = 'fa-close'
      isExpanded = true

      $calcWrapper
        .attr('aria-hidden', 'false')
      # TODO: Investigate why doing this without the timeout causes it to jump
      # down to the bottom of the page. I suspect it's because it's putting the
      # focus on the text field before it transitions onto the page.
      setTimeout (-> $calcWrapper.find('#calculator_input').focus()), 100

    $calc
      .attr
        'title': text
        'aria-expanded': isExpanded
      .find('.utility-control-label').text text
      
    $calc
      .find('.icon')
      .removeClass('fa-calculator')
      .removeClass('fa-close')
      .addClass(icon)

    $calc.toggleClass 'closed'
    
  inputClickHandler: ->
    $('#calculator_output').removeClass('has-result')

  showHint: ->
    @hintPopup
      .addClass('shown')
      .attr('aria-hidden', false)

    $('#calculator_output').removeClass('has-result')

    $(document).on('click', @handleClickOnDocument)

  hideHint: ->
    @hintPopup
      .removeClass('shown')
      .attr('aria-hidden', true)
      
    $('#calculator_output').removeClass('has-result')

    $(document).off('click', @handleClickOnDocument)

  selectHint: (element) ->
    if not element or (element and element.length == 0)
      element = @hintsList.first()

    @activeHint = element;
    @activeHint.focus();
    @hintPopup.attr('data-calculator-hint', element.attr('id'));

  prevHint: () ->
    prev = @activeHint.prev(); # the previous hint
    # if this was the first item
    # select the last one in the group.
    if @activeHint.index() == 0
      prev = @hintsList.last()
    # select the previous hint
    @selectHint(prev)

  nextHint: () ->
    next = @activeHint.next(); # the next hint
    # if this was the last item,
    # select the first one in the group.
    if @activeHint.index() == @hintsList.length - 1
      next = @hintsList.first()
    # give the next hint focus
    @selectHint(next)

  handleKeyDown: (e) ->
    if e.altKey
      # do nothing
      return true

    if e.keyCode == @KEY.ENTER or e.keyCode == @KEY.SPACE
      if @hintPopup.hasClass 'shown'
          @hideHint()
      else
        @showHint()
        @activeHint.focus()

      e.preventDefault()
      return false

    # allow the event to propagate
    return true

  handleKeyDownOnHint: (e) ->
    if e.altKey
      # do nothing
      return true

    switch e.keyCode

      when @KEY.ESC
        # hide popup with hints
        @hideHint()
        @hintButton.focus()

        e.stopPropagation()
        return false

      when @KEY.LEFT, @KEY.UP
        if e.shiftKey
           # do nothing
          return true

        @prevHint()

        e.stopPropagation()
        return false

      when @KEY.RIGHT, @KEY.DOWN
        if e.shiftKey
          # do nothing
          return true

        @nextHint()

        e.stopPropagation()
        return false

    # allow the event to propagate
    return true

  handleKeyUpOnHint: (e) ->
    switch e.keyCode
      when @KEY.TAB
        # move focus to hint links and hide hint once focus is out of hint pop up
        @active_element = document.activeElement
        if not $(@active_element).parents().is(@hintPopup)
          @hideHint()

  handleClickOnDocument: (e) ->
    @hideHint()

  handleClickOnHintButton: (e) ->
    e.preventDefault()
    e.stopPropagation()
    if @hintPopup.hasClass 'shown'
      @hideHint()
      @hintButton.attr('aria-expanded', false)
    else
      @showHint()
      @hintButton.attr('aria-expanded', true)
      @activeHint.focus()

  handleClickOnHintPopup: (e) ->
    e.stopPropagation()

  calculate: ->
    $.getWithPrefix '/calculate', { equation: $('#calculator_input').val() }, (data) ->
      $('#calculator_output')
        .val(data.result)
        .addClass('has-result')
        .focus()
