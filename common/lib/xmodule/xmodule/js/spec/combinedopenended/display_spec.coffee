describe 'CombinedOpenEnded', ->
  beforeEach ->
    spyOn Logger, 'log'
    # load up some fixtures
    loadFixtures 'combined-open-ended.html'
    @element = $('.combined-open-ended')


  describe 'constructor', ->
    beforeEach ->
      @combined = new CombinedOpenEnded @element
    it 'set the element', ->
      expect(@combined.element).toEqual @element


