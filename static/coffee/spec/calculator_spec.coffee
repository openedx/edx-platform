describe 'Calculator', ->
  beforeEach ->
    loadFixtures 'calculator.html'
    @calculator = new Calculator

  describe 'bind', ->
    beforeEach ->
      Calculator.bind()

    it 'bind the calculator button', ->
      expect($('.calc')).toHandleWith 'click', @calculator.toggle

    it 'bind the help button', ->
      # These events are bind by $.hover()
      expect($('div.help-wrapper a')).toHandleWith 'mouseenter', @calculator.helpToggle
      expect($('div.help-wrapper a')).toHandleWith 'mouseleave', @calculator.helpToggle

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
    it 'toggle the calculator and focus the input', ->
      spyOn $.fn, 'focus'
      @calculator.toggle()

      expect($('li.calc-main')).toHaveClass('open')
      expect($('#calculator_wrapper #calculator_input').focus).toHaveBeenCalled()

    it 'toggle the close button on the calculator button', ->
      @calculator.toggle()
      expect($('.calc')).toHaveClass('closed')

      @calculator.toggle()
      expect($('.calc')).not.toHaveClass('closed')

  describe 'helpToggle', ->
    it 'toggle the help overlay', ->
      @calculator.helpToggle()
      expect($('.help')).toHaveClass('shown')

      @calculator.helpToggle()
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
