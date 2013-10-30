describe 'Calculator', ->
  beforeEach ->
    loadFixtures 'coffee/fixtures/calculator.html'
    @calculator = new Calculator

  describe 'bind', ->
    it 'bind the calculator button', ->
      expect($('.calc')).toHandleWith 'click', @calculator.toggle

    it 'bind the help button', ->
      # These events are bind by $.hover()
      expect($('div.help-wrapper a')).toHandle 'mouseover'
      expect($('div.help-wrapper a')).toHandle 'mouseout'
      expect($('div.help-wrapper')).toHandle 'focusin'
      expect($('div.help-wrapper')).toHandle 'focusout'

    it 'prevent default behavior on help button', ->
      $('div.help-wrapper a').click (e) ->
        expect(e.isDefaultPrevented()).toBeTruthy()
      $('div.help-wrapper a').click()

    it 'bind the calculator submit', ->
      expect($('form#calculator')).toHandleWith 'submit', @calculator.calculate

    it 'prevent default behavior on form submit', ->
      jasmine.stubRequests()
      $('form#calculator').submit (e) ->
        expect(e.isDefaultPrevented()).toBeTruthy()
        e.preventDefault()
      $('form#calculator').submit()

  describe 'toggle', ->
    it 'focuses the input when toggled', ->

      # Since the focus is called asynchronously, we need to
      # wait until focus() is called.
      didFocus = false
      runs ->
          spyOn($.fn, 'focus').andCallFake (elementName) -> didFocus = true
          @calculator.toggle(jQuery.Event("click"))

      waitsFor (-> didFocus), "focus() should have been called on the input", 1000

      runs ->
          expect($('#calculator_wrapper #calculator_input').focus).toHaveBeenCalled()

    it 'toggle the close button on the calculator button', ->
      @calculator.toggle(jQuery.Event("click"))
      expect($('.calc')).toHaveClass('closed')

      @calculator.toggle(jQuery.Event("click"))
      expect($('.calc')).not.toHaveClass('closed')

  describe 'helpShow', ->
    it 'show the help overlay', ->
      @calculator.helpShow()
      expect($('.help')).toHaveClass('shown')

  describe 'helpHide', ->
    it 'show the help overlay', ->
      @calculator.helpHide()
      expect($('.help')).not.toHaveClass('shown')

  describe 'calculate', ->
    beforeEach ->
      $('#calculator_input').val '1+2'
      spyOn($, 'getWithPrefix').andCallFake (url, data, callback) ->
        callback({ result: 3 })
      @calculator.calculate()

    it 'send data to /calculate', ->
      expect($.getWithPrefix).toHaveBeenCalledWith '/calculate',
        equation: '1+2'
      , jasmine.any(Function)

    it 'update the calculator output', ->
      expect($('#calculator_output').val()).toEqual('3')
