describe 'CombinedOpenEnded', ->
  beforeEach ->
    spyOn Logger, 'log'
    # load up some fixtures
    loadFixtures 'combined-open-ended.html'
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

