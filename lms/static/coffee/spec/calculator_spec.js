describe 'Calculator', ->

  KEY =
    TAB   : 9
    ENTER : 13
    ALT   : 18
    ESC   : 27
    SPACE : 32
    LEFT  : 37
    UP    : 38
    RIGHT : 39
    DOWN  : 40

  beforeEach ->
    loadFixtures 'coffee/fixtures/calculator.html'
    @calculator = new Calculator

  describe 'bind', ->
    it 'bind the calculator button', ->
      expect($('.calc')).toHandleWith 'click', @calculator.toggle

    it 'bind key up on calculator', ->
      expect($('#calculator_wrapper')).toHandle 'keyup', @calculator.handleKeyUpOnHint

    it 'bind the help button', ->
      # This events is bind by $.click()
      expect($('#calculator_hint')).toHandle 'click'

    it 'bind the calculator submit', ->
      expect($('form#calculator')).toHandleWith 'submit', @calculator.calculate

    xit 'prevent default behavior on form submit', ->
      jasmine.stubRequests()
      $('form#calculator').submit (e) ->
        expect(e.isDefaultPrevented()).toBeTruthy()
        e.preventDefault()
      $('form#calculator').submit()

  describe 'toggle', ->
    it 'focuses the input when toggled', (done)->

      self = this
      focus = ()->
        deferred = $.Deferred()

        # Since the focus is called asynchronously, we need to
        # wait until focus() is called.
        spyOn($.fn, 'focus').and.callFake (elementName) ->
          deferred.resolve()

        self.calculator.toggle(jQuery.Event("click"))

      	 deferred.promise()

      focus().then(
        ->
        	expect($('#calculator_wrapper #calculator_input').focus).toHaveBeenCalled()
      ).always(done)

    it 'toggle the close button on the calculator button', ->
      @calculator.toggle(jQuery.Event("click"))
      expect($('.calc')).toHaveClass('closed')

      @calculator.toggle(jQuery.Event("click"))
      expect($('.calc')).not.toHaveClass('closed')

  describe 'showHint', ->
    it 'show the help overlay', ->
      @calculator.showHint()
      expect($('.help')).toHaveClass('shown')
      expect($('.help')).toHaveAttr('aria-hidden', 'false')


  describe 'hideHint', ->
    it 'show the help overlay', ->
      @calculator.hideHint()
      expect($('.help')).not.toHaveClass('shown')
      expect($('.help')).toHaveAttr('aria-hidden', 'true')

  describe 'handleClickOnHintButton', ->
    it 'on click hint button hint popup becomes visible ', ->
      e = jQuery.Event('click');
      $('#calculator_hint').trigger(e);
      expect($('.help')).toHaveClass 'shown'

  describe 'handleClickOnDocument', ->
    it 'on click out of the hint popup it becomes hidden', ->
      @calculator.showHint()
      e = jQuery.Event('click');
      $(document).trigger(e);
      expect($('.help')).not.toHaveClass 'shown'

  describe 'handleClickOnHintPopup', ->
    it 'on click of hint popup it remains visible', ->
      @calculator.showHint()
      e = jQuery.Event('click');
      $('#calculator_input_help').trigger(e);
      expect($('.help')).toHaveClass 'shown'

  describe 'selectHint', ->
    it 'select correct hint item', ->
      spyOn($.fn, 'focus')
      element = $('.hint-item').eq(1)
      @calculator.selectHint(element)

      expect(element.focus).toHaveBeenCalled()
      expect(@calculator.activeHint).toEqual(element)
      expect(@calculator.hintPopup).toHaveAttr('data-calculator-hint', element.attr('id'))

    it 'select the first hint if argument element is not passed', ->
          @calculator.selectHint()
          expect(@calculator.activeHint.attr('id')).toEqual($('.hint-item').first().attr('id'))

    it 'select the first hint if argument element is empty', ->
          @calculator.selectHint([])
          expect(@calculator.activeHint.attr('id')).toBe($('.hint-item').first().attr('id'))

  describe 'prevHint', ->

    it 'Prev hint item is selected', ->
      @calculator.activeHint = $('.hint-item').eq(1)
      @calculator.prevHint()

      expect(@calculator.activeHint.attr('id')).toBe($('.hint-item').eq(0).attr('id'))

    it 'if this was the second item, select the first one', ->
      @calculator.activeHint = $('.hint-item').eq(1)
      @calculator.prevHint()

      expect(@calculator.activeHint.attr('id')).toBe($('.hint-item').eq(0).attr('id'))

    it 'if this was the first item, select the last one', ->
      @calculator.activeHint = $('.hint-item').eq(0)
      @calculator.prevHint()

      expect(@calculator.activeHint.attr('id')).toBe($('.hint-item').eq(2).attr('id'))

    it 'if this was the last item, select the second last', ->
      @calculator.activeHint = $('.hint-item').eq(2)
      @calculator.prevHint()

      expect(@calculator.activeHint.attr('id')).toBe($('.hint-item').eq(1).attr('id'))

  describe 'nextHint', ->

    it 'if this was the first item, select the second one', ->
      @calculator.activeHint = $('.hint-item').eq(0)
      @calculator.nextHint()

      expect(@calculator.activeHint.attr('id')).toBe($('.hint-item').eq(1).attr('id'))

    it 'If this was the second item, select the last one', ->
      @calculator.activeHint = $('.hint-item').eq(1)
      @calculator.nextHint()

      expect(@calculator.activeHint.attr('id')).toBe($('.hint-item').eq(2).attr('id'))

    it 'If this was the last item, select the first one', ->
      @calculator.activeHint = $('.hint-item').eq(2)
      @calculator.nextHint()

      expect(@calculator.activeHint.attr('id')).toBe($('.hint-item').eq(0).attr('id'))

  describe 'handleKeyDown', ->
    assertHintIsHidden = (calc, key) ->
      spyOn(calc, 'hideHint')
      calc.showHint()
      e = jQuery.Event('keydown', { keyCode: key });
      value = calc.handleKeyDown(e)

      expect(calc.hideHint).toHaveBeenCalled
      expect(value).toBeFalsy()
      expect(e.isDefaultPrevented()).toBeTruthy()

    assertHintIsVisible = (calc, key) ->
      spyOn(calc, 'showHint')
      spyOn($.fn, 'focus')
      e = jQuery.Event('keydown', { keyCode: key });
      value = calc.handleKeyDown(e)

      expect(calc.showHint).toHaveBeenCalled
      expect(value).toBeFalsy()
      expect(e.isDefaultPrevented()).toBeTruthy()
      expect(calc.activeHint.focus).toHaveBeenCalled()

    assertNothingHappens = (calc, key) ->
      spyOn(calc, 'showHint')
      e = jQuery.Event('keydown', { keyCode: key });
      value = calc.handleKeyDown(e)

      expect(calc.showHint).not.toHaveBeenCalled
      expect(value).toBeTruthy()
      expect(e.isDefaultPrevented()).toBeFalsy()

    it 'hint popup becomes hidden on press ENTER', ->
      assertHintIsHidden(@calculator, KEY.ENTER)

    it 'hint popup becomes visible on press ENTER', ->
      assertHintIsVisible(@calculator, KEY.ENTER)

    it 'hint popup becomes hidden on press SPACE', ->
      assertHintIsHidden(@calculator, KEY.SPACE)

    it 'hint popup becomes visible on press SPACE', ->
      assertHintIsVisible(@calculator, KEY.SPACE)

    it 'Nothing happens on press ALT', ->
      assertNothingHappens(@calculator, KEY.ALT)

    it 'Nothing happens on press any other button', ->
      assertNothingHappens(@calculator, KEY.DOWN)

  describe 'handleKeyDownOnHint', ->
    it 'Navigation works in proper way', ->
      calc = @calculator

      eventToShowHint = jQuery.Event('keydown', { keyCode: KEY.ENTER } );
      $('#calculator_hint').trigger(eventToShowHint);

      spyOn(calc, 'hideHint')
      spyOn(calc, 'prevHint')
      spyOn(calc, 'nextHint')
      spyOn($.fn, 'focus')

      cases =
        left:
          event:
            keyCode: KEY.LEFT
            shiftKey: false
          returnedValue: false
          called:
            'prevHint': calc
          isPropagationStopped: true

        leftWithShift:
          returnedValue: true
          event:
            keyCode: KEY.LEFT
            shiftKey: true
          not_called:
            'prevHint': calc

        up:
          event:
            keyCode: KEY.UP
            shiftKey: false
          returnedValue: false
          called:
            'prevHint': calc
          isPropagationStopped: true

        upWithShift:
          returnedValue: true
          event:
            keyCode: KEY.UP
            shiftKey: true
          not_called:
            'prevHint': calc

        right:
          event:
            keyCode: KEY.RIGHT
            shiftKey: false
          returnedValue: false
          called:
            'nextHint': calc
          isPropagationStopped: true

        rightWithShift:
          returnedValue: true
          event:
            keyCode: KEY.RIGHT
            shiftKey: true
          not_called:
            'nextHint': calc

        down:
          event:
            keyCode: KEY.DOWN
            shiftKey: false
          returnedValue: false
          called:
            'nextHint': calc
          isPropagationStopped: true

        downWithShift:
          returnedValue: true
          event:
            keyCode: KEY.DOWN
            shiftKey: true
          not_called:
            'nextHint': calc

        esc:
          returnedValue: false
          event:
            keyCode: KEY.ESC
            shiftKey: false
          called:
            'hideHint': calc
            'focus': $.fn
          isPropagationStopped: true

        alt:
          returnedValue: true
          event:
            which: KEY.ALT
          not_called:
            'hideHint': calc
            'nextHint': calc
            'prevHint': calc

      $.each(cases, (key, data) ->
        calc.hideHint.calls.reset()
        calc.prevHint.calls.reset()
        calc.nextHint.calls.reset()
        $.fn.focus.calls.reset()

        e = jQuery.Event('keydown', data.event or {});
        value = calc.handleKeyDownOnHint(e)

        if data.called
          $.each(data.called, (method, obj) ->
            expect(obj[method]).toHaveBeenCalled()
          )

        if data.not_called
          $.each(data.not_called, (method, obj) ->
            expect(obj[method]).not.toHaveBeenCalled()
          )

        if data.isPropagationStopped
          expect(e.isPropagationStopped()).toBeTruthy()
        else
          expect(e.isPropagationStopped()).toBeFalsy()

        expect(value).toBe(data.returnedValue)
      )

  describe 'calculate', ->
    beforeEach ->
      $('#calculator_input').val '1+2'
      spyOn($, 'getWithPrefix').and.callFake (url, data, callback) ->
        callback({ result: 3 })
      @calculator.calculate()

    it 'send data to /calculate', ->
      expect($.getWithPrefix).toHaveBeenCalledWith '/calculate',
        equation: '1+2'
      , jasmine.any(Function)

    it 'update the calculator output', ->
      expect($('#calculator_output').val()).toEqual('3')
