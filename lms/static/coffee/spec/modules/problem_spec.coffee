describe 'Problem', ->
  beforeEach ->
    # Stub MathJax
    window.MathJax =
      Hub: jasmine.createSpyObj('MathJax.Hub', ['getAllJax', 'Queue'])
      Callback: jasmine.createSpyObj('MathJax.Callback', ['After'])
    @stubbedJax = root: jasmine.createSpyObj('jax.root', ['toMathML'])
    MathJax.Hub.getAllJax.andReturn [@stubbedJax]
    window.update_schematics = ->

    loadFixtures 'problem.html'
    spyOn Logger, 'log'
    spyOn($.fn, 'load').andCallFake (url, callback) ->
      $(@).html readFixtures('problem_content.html')
      callback()

  describe 'constructor', ->
    beforeEach ->
      @problem = new Problem 1, '/problem/url/'

    it 'set the element', ->
      expect(@problem.element).toBe '#problem_1'

    it 'set the content url', ->
      expect(@problem.content_url).toEqual '/problem/url/problem_get?id=1'

    it 'render the content', ->
      expect($.fn.load).toHaveBeenCalledWith @problem.content_url, @problem.bind

  describe 'bind', ->
    beforeEach ->
      spyOn window, 'update_schematics'
      MathJax.Hub.getAllJax.andReturn [@stubbedJax]
      @problem = new Problem 1, '/problem/url/'

    it 'set mathjax typeset', ->
      expect(MathJax.Hub.Queue).toHaveBeenCalled()

    it 'update schematics', ->
      expect(window.update_schematics).toHaveBeenCalled()

    it 'bind answer refresh on button click', ->
      expect($('section.action input:button')).toHandleWith 'click', @problem.refreshAnswers

    it 'bind the check button', ->
      expect($('section.action input.check')).toHandleWith 'click', @problem.check

    it 'bind the reset button', ->
      expect($('section.action input.reset')).toHandleWith 'click', @problem.reset

    it 'bind the show button', ->
      expect($('section.action input.show')).toHandleWith 'click', @problem.show

    it 'bind the save button', ->
      expect($('section.action input.save')).toHandleWith 'click', @problem.save

    it 'bind the math input', ->
      expect($('input.math')).toHandleWith 'keyup', @problem.refreshMath

    it 'display the math input', ->
      expect(@stubbedJax.root.toMathML).toHaveBeenCalled()

  describe 'render', ->
    beforeEach ->
      @problem = new Problem 1, '/problem/url/'
      @bind = @problem.bind
      spyOn @problem, 'bind'

    describe 'with content given', ->
      beforeEach ->
        @problem.render 'Hello World'

      it 'render the content', ->
        expect(@problem.element.html()).toEqual 'Hello World'

      it 're-bind the content', ->
        expect(@problem.bind).toHaveBeenCalled()

    describe 'with no content given', ->
      it 'load the content via ajax', ->
        expect($.fn.load).toHaveBeenCalledWith @problem.content_url, @bind

  describe 'check', ->
    beforeEach ->
      jasmine.stubRequests()
      @problem = new Problem 1, '/problem/url/'
      @problem.answers = 'foo=1&bar=2'

    it 'log the problem_check event', ->
      @problem.check()
      expect(Logger.log).toHaveBeenCalledWith 'problem_check', 'foo=1&bar=2'

    it 'submit the answer for check', ->
      spyOn $, 'postWithPrefix'
      @problem.check()
      expect($.postWithPrefix).toHaveBeenCalledWith '/modx/problem/1/problem_check', 'foo=1&bar=2', jasmine.any(Function)

    describe 'when the response is correct', ->
      it 'call render with returned content', ->
        spyOn($, 'postWithPrefix').andCallFake (url, answers, callback) -> callback(success: 'correct', contents: 'Correct!')
        @problem.check()
        expect(@problem.element.html()).toEqual 'Correct!'

    describe 'when the response is incorrect', ->
      it 'call render with returned content', ->
        spyOn($, 'postWithPrefix').andCallFake (url, answers, callback) -> callback(success: 'incorrect', contents: 'Correct!')
        @problem.check()
        expect(@problem.element.html()).toEqual 'Correct!'

    describe 'when the response is undetermined', ->
      it 'alert the response', ->
        spyOn window, 'alert'
        spyOn($, 'postWithPrefix').andCallFake (url, answers, callback) -> callback(success: 'Number Only!')
        @problem.check()
        expect(window.alert).toHaveBeenCalledWith 'Number Only!'

  describe 'reset', ->
    beforeEach ->
      jasmine.stubRequests()
      @problem = new Problem 1, '/problem/url/'

    it 'log the problem_reset event', ->
      @problem.answers = 'foo=1&bar=2'
      @problem.reset()
      expect(Logger.log).toHaveBeenCalledWith 'problem_reset', 'foo=1&bar=2'

    it 'POST to the problem reset page', ->
      spyOn $, 'postWithPrefix'
      @problem.reset()
      expect($.postWithPrefix).toHaveBeenCalledWith '/modx/problem/1/problem_reset', { id: 1 }, jasmine.any(Function)

    it 'render the returned content', ->
      spyOn($, 'postWithPrefix').andCallFake (url, answers, callback) -> callback("Reset!")
      @problem.reset()
      expect(@problem.element.html()).toEqual 'Reset!'

  describe 'show', ->
    beforeEach ->
      jasmine.stubRequests()
      @problem = new Problem 1, '/problem/url/'
      @problem.element.prepend '<div id="answer_1_1" /><div id="answer_1_2" />'

    describe 'when the answer has not yet shown', ->
      beforeEach ->
        @problem.element.removeClass 'showed'

      it 'log the problem_show event', ->
        @problem.show()
        expect(Logger.log).toHaveBeenCalledWith 'problem_show', problem: 1

      it 'fetch the answers', ->
        spyOn $, 'postWithPrefix'
        @problem.show()
        expect($.postWithPrefix).toHaveBeenCalledWith '/modx/problem/1/problem_show', jasmine.any(Function)

      it 'show the answers', ->
        spyOn($, 'postWithPrefix').andCallFake (url, callback) -> callback('1_1': 'One', '1_2': 'Two')
        @problem.show()
        expect($('#answer_1_1')).toHaveHtml 'One'
        expect($('#answer_1_2')).toHaveHtml 'Two'

      it 'toggle the show answer button', ->
        spyOn($, 'postWithPrefix').andCallFake (url, callback) -> callback({})
        @problem.show()
        expect($('.show')).toHaveValue 'Hide Answer'

      it 'add the showed class to element', ->
        spyOn($, 'postWithPrefix').andCallFake (url, callback) -> callback({})
        @problem.show()
        expect(@problem.element).toHaveClass 'showed'

      describe 'multiple choice question', ->
        beforeEach ->
          @problem.element.prepend '''
            <label for="input_1_1_1"><input type="checkbox" name="input_1_1" id="input_1_1_1" value="1"> One</label>
            <label for="input_1_1_2"><input type="checkbox" name="input_1_1" id="input_1_1_2" value="2"> Two</label>
            <label for="input_1_1_3"><input type="checkbox" name="input_1_1" id="input_1_1_3" value="3"> Three</label>
            <label for="input_1_2_1"><input type="radio" name="input_1_2" id="input_1_2_1" value="1"> Other</label>
          '''

        it 'set the correct_answer attribute on the choice', ->
          spyOn($, 'postWithPrefix').andCallFake (url, callback) -> callback('1_1': [2, 3])
          @problem.show()
          expect($('label[for="input_1_1_1"]')).not.toHaveAttr 'correct_answer', 'true'
          expect($('label[for="input_1_1_2"]')).toHaveAttr 'correct_answer', 'true'
          expect($('label[for="input_1_1_3"]')).toHaveAttr 'correct_answer', 'true'
          expect($('label[for="input_1_2_1"]')).not.toHaveAttr 'correct_answer', 'true'

    describe 'when the answers are alreay shown', ->
      beforeEach ->
        @problem.element.addClass 'showed'
        @problem.element.prepend '''
          <label for="input_1_1_1" correct_answer="true">
            <input type="checkbox" name="input_1_1" id="input_1_1_1" value="1" />
            One
          </label>
        '''
        $('#answer_1_1').html('One')
        $('#answer_1_2').html('Two')

      it 'hide the answers', ->
        @problem.show()
        expect($('#answer_1_1')).toHaveHtml ''
        expect($('#answer_1_2')).toHaveHtml ''
        expect($('label[for="input_1_1_1"]')).not.toHaveAttr 'correct_answer'

      it 'toggle the show answer button', ->
        @problem.show()
        expect($('.show')).toHaveValue 'Show Answer'

      it 'remove the showed class from element', ->
        @problem.show()
        expect(@problem.element).not.toHaveClass 'showed'

  describe 'save', ->
    beforeEach ->
      jasmine.stubRequests()
      @problem = new Problem 1, '/problem/url/'
      @problem.answers = 'foo=1&bar=2'

    it 'log the problem_save event', ->
      @problem.save()
      expect(Logger.log).toHaveBeenCalledWith 'problem_save', 'foo=1&bar=2'

    it 'POST to save problem', ->
      spyOn $, 'postWithPrefix'
      @problem.save()
      expect($.postWithPrefix).toHaveBeenCalledWith '/modx/problem/1/problem_save', 'foo=1&bar=2', jasmine.any(Function)

    it 'alert to the user', ->
      spyOn window, 'alert'
      spyOn($, 'postWithPrefix').andCallFake (url, answers, callback) -> callback(success: 'OK')
      @problem.save()
      expect(window.alert).toHaveBeenCalledWith 'Saved'

  describe 'refreshMath', ->
    beforeEach ->
      @problem = new Problem 1, '/problem/url/'
      @stubbedJax.root.toMathML.andReturn '<MathML>'
      $('#input_example_1').val 'E=mc^2'

    describe 'when there is no exception', ->
      beforeEach ->
        @problem.refreshMath target: $('#input_example_1').get(0)

      it 'should convert and display the MathML object', ->
        expect(MathJax.Hub.Queue).toHaveBeenCalledWith ['Text', @stubbedJax, 'E=mc^2']

      it 'should display debug output in hidden div', ->
        expect($('#input_example_1_dynamath')).toHaveValue '<MathML>'

    describe 'when there is an exception', ->
      beforeEach ->
        @stubbedJax.root.toMathML.andThrow {restart: true}
        @problem.refreshMath target: $('#input_example_1').get(0)

      it 'should queue up the exception', ->
        expect(MathJax.Callback.After).toHaveBeenCalledWith [@problem.refreshMath, @stubbedJax], true

  describe 'refreshAnswers', ->
    beforeEach ->
      @problem = new Problem 1, '/problem/url/'
      @problem.element.html '''
        <textarea class="CodeMirror" />
        <input id="input_1_1" name="input_1_1" class="schematic" value="one" />
        <input id="input_1_2" name="input_1_2" value="two" />
        <input id="input_bogus_3" name="input_bogus_3" value="three" />
        '''
      @stubSchematic = { update_value: jasmine.createSpy('schematic') }
      @stubCodeMirror = { save: jasmine.createSpy('CodeMirror') }
      $('input.schematic').get(0).schematic = @stubSchematic
      $('textarea.CodeMirror').get(0).CodeMirror = @stubCodeMirror

    it 'update each schematic', ->
      @problem.refreshAnswers()
      expect(@stubSchematic.update_value).toHaveBeenCalled()

    it 'update each code block', ->
      @problem.refreshAnswers()
      expect(@stubCodeMirror.save).toHaveBeenCalled()

    it 'serialize all answers', ->
      @problem.refreshAnswers()
      expect(@problem.answers).toEqual "input_1_1=one&input_1_2=two"
