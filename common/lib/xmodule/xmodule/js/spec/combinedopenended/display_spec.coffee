describe 'CombinedOpenEnded', ->
  beforeEach ->
    spyOn Logger, 'log'
    # load up some fixtures
    loadFixtures 'combined-open-ended.html'
    jasmine.Clock.useMock()
    @element = $('.course-content')


  describe 'constructor', ->
    beforeEach ->
      spyOn(Collapsible, 'setCollapsibles')
      @combined = new CombinedOpenEnded @element

    it 'set the element', ->
      expect(@combined.element).toEqual @element

    it 'get the correct values from data fields', ->
      expect(@combined.ajax_url).toEqual '/courses/MITx/6.002x/2012_Fall/modx/i4x://MITx/6.002x/combinedopenended/CombinedOE'
      expect(@combined.state).toEqual 'assessing'
      expect(@combined.task_count).toEqual 2
      expect(@combined.task_number).toEqual 2

    it 'subelements are made collapsible', -> 
      expect(Collapsible.setCollapsibles).toHaveBeenCalled()

    it 'elements are rebound for assessing state', ->
      expect(@combined.answer_area.attr("disabled")).toBe("disabled")
      expect(@combined.submit_button.val()).toBe("Submit assessment")

  describe 'poll', ->
    beforeEach =>
      # setup the spies
      @combined = new CombinedOpenEnded @element
      spyOn(@combined, 'reload').andCallFake -> return 0
      window.setTimeout = jasmine.createSpy().andCallFake (callback, timeout) -> return 5

    it 'we are setting the timeout', =>
      fakeResponseContinue = state: 'not done'
      spyOn($, 'postWithPrefix').andCallFake (url, callback) -> callback(fakeResponseContinue)
      @combined.poll()
      expect(window.setTimeout).toHaveBeenCalledWith(@combined.poll, 10000)
      expect(window.queuePollerID).toBe(5)

    it 'we are stopping polling properly', =>
      $.postWithPrefix = jasmine.createSpy("$.postWithPrefix")
      fakeResponseDone = state: "done" 
      $.postWithPrefix.andCallFake (url, callback) -> callback(fakeResponseDone)
      @combined.poll()
      expect(window.queuePollerID).toBeUndefined()
      expect(window.setTimeout).not.toHaveBeenCalled()
      expect(@combined.reload).toHaveBeenCalled()
