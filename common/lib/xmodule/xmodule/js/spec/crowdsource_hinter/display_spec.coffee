describe 'Crowdsourced hinter', ->
  beforeEach ->
    window.update_schematics = ->
    jasmine.stubRequests()
    # note that the fixturesPath is set in spec/helper.coffee
    loadFixtures 'crowdsource_hinter.html'
    @hinter = new Hinter($('#hinter-root'))

  describe 'high-level integration tests', ->
    # High-level, happy-path tests for integration with capa problems.
    beforeEach ->
      # Make a more thorough $.postWithPrefix mock.
      spyOn($, 'postWithPrefix').andCallFake( ->
        last_argument = arguments[arguments.length - 1]
        if typeof last_argument == 'function'
          response =
            success: 'incorrect'
            contents: 'mock grader response'
          last_argument(response)
          promise =
            always: (callable) -> callable()
            done: (callable) -> callable()
      )
      @problem = new Problem($('#problem'))
      @problem.bind()

    it 'knows when a capa problem is graded, using check.', ->
      @problem.answers = 'test answer'
      @problem.check()
      expect($.postWithPrefix).toHaveBeenCalledWith("#{@hinter.url}/get_hint", 'test answer', jasmine.any(Function))

    it 'knows when a capa problem is graded usig check_fd.', ->
      spyOn($, 'ajaxWithPrefix').andCallFake((url, settings) ->
        response =
          success: 'incorrect'
          contents: 'mock grader response'
        settings.success(response) if settings
      )
      @problem.answers = 'test answer'
      @problem.check_fd()
      expect($.postWithPrefix).toHaveBeenCalledWith("#{@hinter.url}/get_hint", 'test answer', jasmine.any(Function))

  describe 'capture_problem', ->
    beforeEach ->
      spyOn($, 'postWithPrefix').andReturn(null)

    it 'gets hints for an incorrect answer', ->
      data = ['some answers', '<thing class="incorrect">']
      @hinter.capture_problem('problem_graded', data, 'fake element')
      expect($.postWithPrefix).toHaveBeenCalledWith("#{@hinter.url}/get_hint", 'some answers', jasmine.any(Function))

    it 'gets feedback for a correct answer', ->
      data = ['some answers', '<thing class="correct">']
      @hinter.capture_problem('problem_graded', data, 'fake element')
      expect($.postWithPrefix).toHaveBeenCalledWith("#{@hinter.url}/get_feedback", 'some answers', jasmine.any(Function))
