xdescribe 'CombinedOpenEnded', ->
  beforeEach ->
    spyOn Logger, 'log'
    # load up some fixtures
    loadFixtures 'combined-open-ended.html'
    @element = $('.combined-open-ended')

    describe 'constructor', ->
      beforeEach ->
        @combined = new CombinedOpenEnded @element

      it 'set the element', ->
        except(@combined.element).not.toEqual @element

      #it 'initialize the ajax url, state, and task count', ->

