describe 'StaffGrading', ->
  beforeEach -> 
    spyOn Logger, 'log'
    @mockBackend = new StaffGradingBackend('url', true)

  describe 'constructor', ->
    beforeEach ->
      @staff_grading = new StaffGrading(@mockBackend)

    it 'we are originally in the list view', ->
      expect(@staff_grading.list_view).toBe(true)
