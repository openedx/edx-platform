describe 'Annotatable', ->
    beforeEach ->
        loadFixtures 'annotatable.html'
    describe 'constructor', ->
        beforeEach ->
            @annotatable = new Annotatable $('.xmodule_display')
        it 'initializes tooltips', ->
            expect(1).toBe 2
